import unittest
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

from decimal import Decimal

import slcsp


# Data used by the TestSlcsp.test_slcsp integration test
def mock_csv_files(name, newline=""):
    if name == "slcsp.csv":
        return mock_open(
            read_data=("zipcode,rate\n" "36749,\n" "48435,\n" "48126,\n")
        )()

    if name == "zips.csv":
        return mock_open(
            read_data=(
                "zipcode,state,county_code,name,rate_area\n"
                "36749,AL,01001,Autauga,11\n"
                "48435,MI,26087,Lapeer,5\n"
                "48435,MI,26157,Tuscola,6\n"
                "48126,MI,26163,Wayne,1\n"
            )
        )()

    if name == "plans.csv":
        return mock_open(
            read_data=(
                "plan_id,state,metal_level,rate,rate_area\n"
                "36956VI7724021,TX,Silver,310.12,11\n"
                "71371IL9623602,WI,Silver,348.73,11\n"
                "92765TU8433188,FL,Gold,385.88,11\n"
                "52643TK3267610,ME,Silver,305.27,1\n"
            )
        )()


class TestSlcsp(unittest.TestCase):
    def test_get_zipcodes_to_process(self):
        zipcodes = [{"zipcode": "12345"}, {"zipcode": "23456"}]
        self.assertEqual(slcsp.get_zipcodes_to_process(zipcodes), ["12345", "23456"])

    def test_get_zipcodes_to_rate_areas(self):
        zipcodes = ["12345", "23456"]
        zipcode_rate_areas = [
            # should be included
            {"zipcode": "12345", "rate_area": "1"},
            # should be excluded: rate_area is ambiguous
            {"zipcode": "23456", "rate_area": "1"},
            {"zipcode": "23456", "rate_area": "2"},
            # should be excluded: not in zipcodes
            {"zipcode": "34567", "rate_area": "3"},
        ]

        self.assertDictEqual(
            slcsp.get_zipcodes_to_rate_areas(zipcodes, zipcode_rate_areas),
            {
                "12345": "1",
                "23456": None,
            },
        )

    def test_get_slcsps(self):
        plans = [
            # No second highest rate
            {"rate_area": "1", "metal_level": "Silver", "rate": "500"},
            # Gold-level rate should be ignored
            {"rate_area": "2", "metal_level": "Gold", "rate": "600"},
            {"rate_area": "2", "metal_level": "Silver", "rate": "500"},
            {"rate_area": "2", "metal_level": "Silver", "rate": "400"},
            # Not in our mapping of zipcodes to rate areas, so ignored
            {"rate_area": "3", "metal_level": "Silver", "rate": "500"},
            {"rate_area": "3", "metal_level": "Silver", "rate": "400"},
        ]
        zipcode_to_rate_areas = {
            "12345": "1",
            "23456": "2",
        }

        self.assertDictEqual(
            slcsp.get_slcsps(plans, zipcode_to_rate_areas),
            {
                "1": (Decimal("500"), 0),
                "2": (Decimal("500"), Decimal("400")),
            },
        )

    def test_format_slcsps(self):
        zipcodes = ["12345", "23456"]
        zipcode_to_rate_areas = {"12345": "1", "23456": "2"}
        slcsps = {
            "1": (Decimal("500"), 0),
            "2": (Decimal("500"), Decimal("400")),
        }

        self.assertEqual(
            slcsp.format_slcsps(zipcodes, zipcode_to_rate_areas, slcsps),
            [
                # No second-highest rate (and should be printed first)
                "12345,",
                # Second-highest rate should be printed with two decimal places
                "23456,400.00",
            ],
        )

    @patch("sys.stdout", new_callable=StringIO)
    @patch("builtins.open", side_effect=mock_csv_files)
    def test_slcsp(self, mock_open, stdout):
        slcsp.main()

        self.assertEqual(
            stdout.getvalue(),
            # Formatted to two decimal places, ignores non-silver plans
            "36749,310.12\n"
            # Empty because zip code has ambiguous mapping
            "48435,\n"
            # Empty because rate area does not have a second Silver plan
            "48126,\n",
        )
