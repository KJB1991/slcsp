from csv import DictReader
from decimal import Decimal
from collections import defaultdict
from typing import Iterable, Optional


def get_zipcodes_to_process(zipcode_rows: Iterable[dict[str, str]]) -> list[str]:
    """Return a list of zipcodes from an iterable of dictionaries containing entries
    with the key `zipcode`"""
    return [row["zipcode"] for row in zipcode_rows]


def get_zipcodes_to_rate_areas(
    zipcodes_to_process: list[str], zipcode_rate_area_rows: Iterable[dict[str, str]]
):
    """Given a list of zipcodes_to_process and an iterable of dictionaries containing entries
    with the key `zipcode` and `rate_area`, return a mapping from zipcodes to rate areas. Zipcodes
    with more than one matching rate area will have `None` for their rate area."""

    zipcodes_to_process_set = set(zipcodes_to_process)
    zipcodes_to_rate_areas: dict[str, Optional[str]] = {}

    for row in zipcode_rate_area_rows:
        zipcode = row["zipcode"]
        rate_area = row["rate_area"]

        if zipcode in zipcodes_to_process_set:
            # If we already assigned this zipcode a rate area, and this
            # is a different rate area, then the rate area is ambiguous
            if (
                zipcode in zipcodes_to_rate_areas
                and zipcodes_to_rate_areas[zipcode] != rate_area
            ):
                zipcodes_to_rate_areas[zipcode] = None
            else:
                zipcodes_to_rate_areas[zipcode] = rate_area

    return zipcodes_to_rate_areas


def get_slcsps(
    plan_rows: Iterable[dict[str, str]],
    zipcodes_to_rate_areas: dict[str, Optional[str]],
) -> dict[str, tuple[Decimal, Decimal]]:
    """Given an iterable of dictionaries with keys for `metal_level`, `rate_area`, and `rate`,
    and mapping of zipcodes to rate areas, return a dictionary containing the highest and
    second-highest rates for each silver plan for the rate areas in the mapping.
    """

    # Convert to set to make processing faster
    rate_areas = set(zipcodes_to_rate_areas.values())

    # By default, assign the highest and second highest rate for a rate area to zero
    slcsps: dict[str, tuple[Decimal, Decimal]] = defaultdict(
        lambda: (Decimal("0"), Decimal("0"))
    )

    for row in plan_rows:
        if row["metal_level"] == "Silver" and row["rate_area"] in rate_areas:
            rate_area = row["rate_area"]
            rate = Decimal(row["rate"])

            # Is this the highest rate?
            if rate > slcsps[rate_area][0]:
                slcsps[rate_area] = rate, slcsps[rate_area][0]

            # Or the second-highest rate?
            elif rate > slcsps[rate_area][1]:
                slcsps[rate_area] = slcsps[rate_area][0], rate

    return slcsps


def format_slcsps(
    zipcodes: list[str],
    zipcodes_to_rate_areas: dict[str, str],
    slcsps: dict[str, tuple[Decimal, Decimal]],
) -> list[str]:
    """Given an ordered list of zipcodes, a mapping to rate areas, and a dictionary of the highest and second-highest rates of
    the silver plans in those rate areas, return a formatted list of the second highest rate in each zipcode.
    """

    formatted_slcsps = []

    for zipcode in zipcodes:
        rate_area = zipcodes_to_rate_areas[zipcode]
        second_highest_rate = slcsps[rate_area][1]

        if second_highest_rate:
            formatted_slcsps.append(f"{zipcode},{second_highest_rate:.2f}")
        else:
            formatted_slcsps.append(f"{zipcode},")

    return formatted_slcsps


def main() -> None:
    """Print a formatted list of SLCSPs, given a set of zipcodes in slcsp.csv, a
    mapping of zip codes to rate areas in zips.csv, and a set of plans in plans.csv"""

    # Get an ordered list of zipcodes to process
    with open("slcsp.csv", newline="") as slcsp_file:
        slcsp_csv_reader = DictReader(slcsp_file)
        zipcodes = get_zipcodes_to_process(slcsp_csv_reader)

    # Map those zipcodes to their rate areas
    with open("zips.csv", newline="") as zips_file:
        zips_csv_reader = DictReader(zips_file)
        zipcodes_to_rate_areas = get_zipcodes_to_rate_areas(zipcodes, zips_csv_reader)

    # For each rate area, get the SLCSP
    with open("plans.csv", newline="") as plans_file:
        plans_csv_reader = DictReader(plans_file)
        slcsps = get_slcsps(plans_csv_reader, zipcodes_to_rate_areas)

    # Format the SCLSPs per requirements and print
    formatted_slcsps = format_slcsps(zipcodes, zipcodes_to_rate_areas, slcsps)

    for formatted_slcsp in formatted_slcsps:
        print(formatted_slcsp)


if __name__ == "__main__":
    main()
