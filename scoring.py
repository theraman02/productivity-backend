def calculate_productivity(task, speed, professionalism, activity):
    weights = {
        "task": 0.4,
        "speed": 0.2,
        "professionalism": 0.2,
        "activity": 0.2,
    }

    score = (
        task * weights["task"]
        + speed * weights["speed"]
        + professionalism * weights["professionalism"]
        + activity * weights["activity"]
    )

    return round(score, 2)
