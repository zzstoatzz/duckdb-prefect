from random import choice, sample

import duckdb
import httpx
import pandas as pd
from prefect import flow, task
from prefect.tasks import task_input_hash


@task(cache_key_fn=task_input_hash)
async def fetch_pokemon_data(n: int) -> list[dict]:
    """Fetches data for the first n pokemon from the PokeAPI."""
    pokemon_data = []
    async with httpx.AsyncClient() as client:
        for i in range(1, n + 1):
            r = await client.get(f'https://pokeapi.co/api/v2/pokemon/{i}/')
            data = r.json()
            pokemon_data.append({
                'name': data['name'],
                'height': data['height'],
                'weight': data['weight'],
                'base_experience': data['base_experience'],
                'types': ','.join([t['type']['name'] for t in data['types']])
            })
    return pokemon_data

@task
def simulate_single_battle(pair) -> dict[str, str]:
    winner = choice([pair[0]['name'], pair[1]['name']])
    return {'pokemon1': pair[0]['name'], 'pokemon2': pair[1]['name'], 'winner': winner}

@task
def duckdb_analytics(all_battle_results) -> str:
    _battles_df = pd.DataFrame.from_dict(
        [round_results for round_results in all_battle_results]
    )
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE IF NOT EXISTS battles"
        " (pokemon1 STRING, pokemon2 STRING, winner STRING)"
    )
    con.execute("INSERT INTO battles SELECT * FROM _battles_df")
    most_wins = con.execute(
        "SELECT winner, COUNT(*) as wins"
        " FROM battles"
        " GROUP BY winner"
        " ORDER BY wins DESC"
        " LIMIT 1"
    ).fetchone()
    return f"Pokemon with most wins: {most_wins[0]} with {most_wins[1]} win(s)"


@flow
def pokemon_battle_simulation(n_pokemon: int = 100, n_rounds: int = 3):
    pokemon_data = fetch_pokemon_data(n_pokemon)
    all_battle_results = [
        round_results
        for _ in range(n_rounds)
        for round_results in simulate_single_battle.map(
            [
                (permuted[i], permuted[i + 1])
                for permuted in [sample(pokemon_data, len(pokemon_data))]
                for i in range(0, len(pokemon_data), 2)
            ]
        )
    ]

    return duckdb_analytics(all_battle_results)


if __name__ == '__main__':
    result = pokemon_battle_simulation(n_pokemon=10, n_rounds=3)
    print(result)
