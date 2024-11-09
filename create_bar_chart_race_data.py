import sqlite3
import pandas as pd

class CreateBarChartRaceData:
    def adjust_datetime_format(self, x):
        date_part, time_part = x.split()
        date_part = "2024-01-13"
        datetime_iso_8601 = f"{date_part} {time_part}"
        return datetime_iso_8601
    def create_cumulative_votes_by_time_candidate(self):
        connection = sqlite3.connect("data/taiwan_presidential_election_2024.db")
        sql_query = """
        SELECT polling_places.county,
            polling_places.polling_place,
            candidates.candidate,
            SUM(votes.votes) AS sum_votes
        FROM votes
        JOIN candidates
            ON votes.candidate_id = candidates.id
        JOIN polling_places
            ON votes.polling_place_id = polling_places.id
        GROUP BY polling_places.county,
                polling_places.polling_place,
                candidates.candidate;
        """
        votes_by_county_polling_place_candidate = pd.read_sql(sql_query, con=connection)
        connection.close()
        votes_collected = pd.read_excel("data/113全國投開票所完成時間.xlsx", skiprows=[0, 1, 2])
        votes_collected.columns = ["county", "town", "polling_place", "collected_at", "number_of_voters"]
        votes_collected = votes_collected[["county", "town", "polling_place", "collected_at"]]
        merged = pd.merge(votes_by_county_polling_place_candidate, votes_collected,
                        left_on=["county", "polling_place"], right_on=["county", "polling_place"],
                        how="left")
        votes_by_collected_at_candidate = merged.groupby(["collected_at", "candidate"])["sum_votes"].sum().reset_index()
        cum_sum = votes_by_collected_at_candidate.groupby("candidate")["sum_votes"].cumsum()
        votes_by_collected_at_candidate["cumulative_sum_votes"] = cum_sum
        votes_by_collected_at_candidate["collected_at"] = votes_by_collected_at_candidate["collected_at"].map(self.adjust_datetime_format)
        votes_by_collected_at_candidate["collected_at"] = pd.to_datetime(votes_by_collected_at_candidate["collected_at"])
        return votes_by_collected_at_candidate
    def create_covid_19_confirmed(self):
        connection = sqlite3.connect("data/covid_19.db")
        sql_query = """
        SELECT reported_on,
            country,
            confirmed
        FROM time_series
        WHERE reported_on <= "2020-12-31";
        """
        covid_19_confirmed = pd.read_sql(sql_query, con=connection)
        connection.close()
        nlargest_index = covid_19_confirmed.groupby("reported_on")["confirmed"].nlargest(10).reset_index()["level_1"]
        covid_19_confirmed = covid_19_confirmed.loc[nlargest_index, :].reset_index(drop=True)
        return covid_19_confirmed