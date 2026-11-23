from app.tools.destination_search import destination_search


def test_search_returns_activities_whose_interests_match():
    results = destination_search(
        "Japan",
        cities=["Tokyo", "Kyoto"],
        interests=["Japanese food", "technology"],
    )

    by_activity = {item.activity: item for item in results}
    assert set(by_activity) == {
        "teamLab Planets",
        "Tsukiji Outer Market",
        "Nishiki Market",
        "Kyoto Railway Museum",
    }
    assert by_activity["Tsukiji Outer Market"].city == "Tokyo"
    assert by_activity["Tsukiji Outer Market"].matched_interests == ["Japanese food"]
    assert by_activity["teamLab Planets"].matched_interests == ["technology"]
    assert by_activity["Kyoto Railway Museum"].city == "Kyoto"
    assert by_activity["Kyoto Railway Museum"].matched_interests == ["technology"]


def test_search_without_interests_returns_every_activity_in_the_cities():
    results = destination_search("japan", cities=["tokyo"])

    assert [item.activity for item in results] == [
        "teamLab Planets",
        "Tsukiji Outer Market",
        "Senso-ji Temple",
    ]
    assert all(item.matched_interests == [] for item in results)


def test_search_for_an_unknown_destination_is_empty():
    assert destination_search("Mars", interests=["food"]) == []
