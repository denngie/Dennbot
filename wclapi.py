#!/usr/bin/python
"""Attendance class definition."""
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from gql.transport.requests import RequestsHTTPTransport
from gql import Client, gql
from tokencache import gettoken


class WCL:
    """Retrieve data from WCL API."""

    def __init__(self) -> None:
        """Initiate class."""
        url = "https://classic.warcraftlogs.com/api/v2/client"
        token = gettoken()
        transport = RequestsHTTPTransport(url=url, headers={"Authorization": token})
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def _zone_attendance(self, zone: int) -> list[dict[str, Any]]:
        """Retrieve attendance data for WCL zone."""
        query = gql(
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
        data = []
        page = 1
        while page is not False:
            params = {"page": page, "zone": zone}
            result = self.client.execute(query, variable_values=params)
            data += result["guildData"]["guild"]["attendance"]["data"]  # pylint: disable=unsubscriptable-object
            if result["guildData"]["guild"]["attendance"]["has_more_pages"] is True:  # pylint: disable=unsubscriptable-object
                page += 1
            else:
                page = False
        return data

    def _raid_reports(self, zone: int, encounter: int) -> list[str]:
        """Retrieve raid reports for specific encounter."""
        query = gql(
            """
            query ($page: Int, $zone: Int, $encounter: Int) {
                reportData {
                    reports(guildID: 611338, guildTagID: 50758, limit: 100, page: $page, zoneID: $zone) {
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

        encounter_reports: list[str] = []
        page = 1
        while page is not False:
            params = {"page": page, "zone": zone, "encounter": encounter}
            result = self.client.execute(query, variable_values=params)
            for report in result["reportData"]["reports"]["data"]:  # pylint: disable=unsubscriptable-object
                if report["fights"]:
                    encounter_reports.append(report["code"])
            if result["reportData"]["reports"]["has_more_pages"] is True:  # pylint: disable=unsubscriptable-object
                page += 1
            else:
                page = False

        return encounter_reports

    def calculated_attendance(self,
                              zone: int,
                              start_date: str = "",
                              end_date: str = "",
                              encounter: int = 0) -> tuple[dict[str, int], int]:
        """Calculate attendance according to args."""
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
            start_utime = int(start_datetime.replace(tzinfo=timezone.utc).timestamp()) * 1000
        if end_date:
            end_datetime = datetime.fromisoformat(end_date)
            end_utime = int(end_datetime.replace(tzinfo=timezone.utc).timestamp()) * 1000 + 86400000

        players_attendance: dict[str, int] = defaultdict(int)
        total_raids = 0
        attendance_data = self._zone_attendance(zone)
        if encounter:
            encounter_reports = self._raid_reports(zone, encounter)

        for report in attendance_data:
            if start_date and start_utime > report["startTime"]:
                continue
            if end_date and end_utime < report["startTime"]:
                continue
            if encounter and report["code"] not in encounter_reports:
                continue
            for player in report["players"]:
                players_attendance[player["name"]] += 1
            total_raids += 1

        return players_attendance, total_raids
