# | pyright: reportAny=false |

from datetime import datetime, timezone

from tinyflux import Point, TagQuery, TimeQuery, TinyFlux
from tinyflux.queries import Query

from model.cart import Cart


class TimeSeriesDB:
    def __init__(self, db_path: str) -> None:
        self._database = TinyFlux(db_path)

    def get_cart(self, car_id: str, count: int = 10) -> list[Cart]:
        """
        Retrieve a list of Cart objects for a given car_id, limited to a specified count.

        Args:
            car_id (str): The ID of the car to retrieve.
            count (int, optional): The maximum number of Cart objects to retrieve. Defaults to 10.

        Returns:
            list[Cart]: A list of Cart objects.
        """
        Tag = TagQuery()
        query = Tag.id == car_id

        results = self._database.search(query)[-count:]
        car_list = [Cart(**result.fields) for result in results]

        return car_list

    def get_car_after(self, count_by_car: int, date_after: datetime) -> dict[str, list[Cart]]:
        """
        Retrieve a dictionary of Cart objects grouped by car_id, for entries after a specified date.

        Args:
            count_by_car (int): The maximum number of Cart objects to retrieve per car_id.
            date_after (datetime): The date after which to retrieve Cart objects.

        Returns:
            dict[str, list[Cart]]: A dictionary where keys are car_ids and values are lists of Cart objects.
        """
        results = self._database.search(
            TimeQuery() > date_after,
            sorted=True,
        )

        grouped_results: dict[str, list[Cart]] = {}
        wanted_results = results

        wanted_results = sorted(wanted_results, key=lambda x: x.time, reverse=True)
        for result in wanted_results:
            if result.tags["id"] not in grouped_results:
                grouped_results[result.tags["id"]] = []

            if len(grouped_results[result.tags["id"]]) < count_by_car:
                grouped_results[result.tags["id"]].append(Cart(**result.fields))

        return grouped_results

    def get_carts_today(self, count_by_car: int):
        """
        Retrieve a dictionary of Cart objects grouped by car_id, for entries from today.

        Args:
            count_by_car (int): The maximum number of Cart objects to retrieve per car_id.

        Returns:
            dict[str, list[Cart]]: A dictionary where keys are car_ids and values are lists of Cart objects.
        """
        date = datetime.now().replace(minute=0, second=0, microsecond=0).astimezone(timezone.utc)

        return self.get_car_after(count_by_car, date)

    def insert(self, car_id: str, car: Cart) -> None:
        """
        Insert a new data point into the database.

        Args:
            point (Point): The data point to insert.
        """

        point = Point(
            tags={
                "id": car_id,
            },
            fields=car.model_dump(),
        )

        self._database.insert(point)

    def remove(self, query: Query) -> int:
        """
        Remove data points from the database that match the given query.

        Args:
            query (Query): The query to match data points for removal.

        Returns:
            int: The number of data points removed.
        """
        return self._database.remove(query)
