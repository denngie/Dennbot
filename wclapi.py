#!/usr/bin/python
"""Attendance class definition."""
from collections import defaultdict
from datetime import datetime, timezone
from gql.transport.exceptions import TransportServerError
from gql.transport.requests import RequestsHTTPTransport
from gql import Client, gql
from tokencache import gettoken
from settings import ALTS


class WCL:
    """Retrieve data from WCL API."""

    def __init__(self, zone: int, start_date: str, end_date: str, encounter: int) -> None:
        """Initiate class."""
        url = "https://classic.warcraftlogs.com/api/v2/client"
        token = gettoken()
        transport = RequestsHTTPTransport(url=url, headers={"Authorization": token})
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        self.zone = zone
        self.start_date = start_date
        self.end_date = end_date
        self.encounter = encounter
        self.players: dict[str, int] = defaultdict(int)

    def _get_all_results(self, query: str, querytype: str, params: dict[str, int]) -> list:
        """Get all results from query."""
        gqlquery = gql(query)
        data = []
        page = 1

        while page is not False:
            params["page"] = page
            try:
                result = self.client.execute(gqlquery, variable_values=params)
            except TransportServerError as err:
                raise ConnectionError(err) from err

            if querytype == "reportData":
                data += result["reportData"]["reports"]["data"]  # pylint: disable=unsubscriptable-object
                if result["reportData"]["reports"]["has_more_pages"]:  # pylint: disable=unsubscriptable-object
                    page += 1
                else:
                    page = False
            elif querytype == "guildData":
                data += result["guildData"]["guild"]["attendance"]["data"]  # pylint: disable=unsubscriptable-object
                if result["guildData"]["guild"]["attendance"]["has_more_pages"]:  # pylint: disable=unsubscriptable-object
                    page += 1
                else:
                    page = False

        return data

    def _convert_dates(self) -> tuple[int, int]:
        """Convert dates from string to utime."""
        if self.start_date:
            start_datetime = datetime.fromisoformat(self.start_date)
            start_utime = int(start_datetime.replace(tzinfo=timezone.utc).timestamp()) * 1000
        else:
            start_utime = 0
        if self.end_date:
            end_datetime = datetime.fromisoformat(self.end_date)
            end_utime = int(end_datetime.replace(tzinfo=timezone.utc).timestamp()) * 1000 + 86400000
        else:
            end_utime = 9999999999999

        return start_utime, end_utime

    def _encounter_reports(self) -> list[str]:
        """Retrieve raid reports for specific encounter."""
        query = (
            """
            query ($page: Int, $zone: Int, $encounter: Int) {
                reportData {
                    reports(guildID: 611338, guildTagID: 50758, limit: 100,
                            page: $page, zoneID: $zone) {
                        total
                        has_more_pages
                        data {
                            code
                            fights(encounterID: $encounter) {
                                id
                            }
                        }
                    }
                }
            }
        """
        )

        params = {"zone": self.zone, "encounter": self.encounter}
        data = self._get_all_results(query, "reportData", params)
        encounter_reports: list[str] = []

        for report in data:
            if report["fights"]:
                encounter_reports.append(report["code"])

        return encounter_reports

    def _combine_alts(self) -> None:
        """Combine alts attendance to main."""
        for main, alts in ALTS.items():
            for alt in alts:
                if {main, alt} <= self.players.keys():
                    self.players[main] += self.players[alt]
                    self.players.pop(alt)

    def calculate_attendance(self) -> list[str]:
        """Calculate attendance according to args."""
        start_utime, end_utime = self._convert_dates()

        if self.encounter:
            encounter_reports = self._encounter_reports()

        query = (
            """
            query ($page: Int, $zone: Int) {
                guildData {
                    guild(id: 611338) {
                        attendance(guildTagID: 50758, limit: 25, page: $page, zoneID: $zone) {
                            total
                            has_more_pages
                            data {
                                code
                                startTime
                                zone {
                                    id
                                }
                                players {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        """
        )
        params = {"zone": self.zone}
        data = self._get_all_results(query, "guildData", params)
        total_raids = 0

        for report in data:
            if self.start_date and start_utime > report["startTime"]:
                continue
            if self.end_date and end_utime < report["startTime"]:
                continue
            if self.encounter and report["code"] not in encounter_reports:
                continue

            for player in report["players"]:
                self.players[player["name"]] += 1
            total_raids += 1

        self._combine_alts()
        sorted_players: list[str] = []
        for player, value in sorted(self.players.items(), key=lambda item: item[1], reverse=True):
            percentage = value / total_raids * 100
            percentage = min(percentage, 100)
            sorted_players.append(f"{player}: {percentage:.0f}%")
        return sorted_players

    @staticmethod
    def _avg_deaths(death_stats: dict[str, dict]) -> dict[str, float]:
        """Return average deaths per player dict."""
        player_stats: dict[str, float] = {}
        for player, player_stat in death_stats.items():
            if player_stat["reports"] < 5:
                continue
            try:
                avg = float(player_stat['deaths'] / player_stat['reports'])
            except ZeroDivisionError:
                avg = float(0)
            player_stats[player] = avg

        return player_stats

    def calculate_deaths(self) -> dict[str, float]:
        """Retrieve raid reports for specific encounter."""
        start, end = self._convert_dates()

        if self.encounter:
            encounter_reports = self._encounter_reports()

        query = (
            """
            query ($end: Float, $page: Int, $start: Float, $zone: Int) {
                reportData {
                    reports(endTime: $end, guildID: 611338, guildTagID: 50758, limit: 100,
                            page: $page, startTime: $start, zoneID: $zone) {
                        total
                        has_more_pages
                        data {
                            code
                            fights(killType: Wipes) {
                                id
                            }
                            rankedCharacters {
                                name
                            }
                            table(dataType: Deaths, endTime: $end)
                        }
                    }
                }
            }
        """
        )

        params = {"end": end, "start": start, "zone": self.zone}
        data = self._get_all_results(query, "reportData", params)

        death_stats: dict[str, dict] = {}
        for report in data:
            if self.encounter and report["code"] not in encounter_reports:
                continue
            wipes: list[int] = []
            for fight in report["fights"]:
                wipes.append(fight["id"])
            for player in report["rankedCharacters"]:
                if player["name"] not in death_stats:
                    death_stats[player["name"]] = {"reports": 0, "deaths": 0}
                death_stats[player["name"]]["reports"] += 1

            for entry in report["table"]["data"]["entries"]:
                # Ignore priest double deaths due to spirit form
                if all([entry["icon"] == "Priest-Holy",
                        entry["damage"]["abilities"],
                        entry["events"]]):
                    continue

                if entry["fight"] not in wipes:
                    death_stats[entry["name"]]["deaths"] += 1

        return self._avg_deaths(death_stats)
