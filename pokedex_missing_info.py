from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
from typing import Any

def transform_base(base: dict[str, Any]) -> dict[str, Any]:
    return {
        'HP': base['hp'],
        'Attack': base['attack'],
        'Defense': base['defense'],
        'Sp. Attack': base['special_attack'],
        'Sp. Defense': base['special_defense'],
        'Speed': base['speed'],
    }

def update_singularity_file(singularity_file: Path, singularity: list[dict[str, Any]]) -> None:
    with singularity_file.open('w') as f:
        json.dump(singularity, f, indent=2, ensure_ascii=False)
    subprocess.run(("pre-commit", "run", "prettier", "--files", singularity_file))


def create_git_patch(commit_title: str, singularity_file: Path, pokemon_source: dict[str, Any]):
    run_cmd("git", "add", singularity_file)
    run_cmd("git", "commit", "--file=-", stdin=f"{commit_title}\n\nValue is from <{pokemon_source['url']}>".encode())

def run_cmd(*cmd: str | Path, stdin: bytes | None = None) -> None:
    print(f">> {' '.join(map(str, cmd))}")
    res = subprocess.run(cmd, input=stdin)
    assert res.returncode == 0


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--singularity', type=Path, default=Path('pokedex.json'))
    args = parser.parse_args()

    source_file: Path = args.source
    singularity_file: Path = args.singularity

    with source_file.open('r') as f:
        source = json.load(f)

    with singularity_file.open('r') as f:
        singularity = json.load(f)

    for pokemon in singularity:
        updated = False
        pokemon_source = source[str(pokemon['id'])]
        pokemon_id = f"{pokemon['name']['english'].title()}:{pokemon['id']:04}"
        pokemon_name = pokemon['name']['english'].lower().replace(' ', '-')

        pokemon_base = transform_base(pokemon_source['base'])

        if pokemon.get('base') is None:
            commit_title = f"Add base to `{pokemon_name.title()}`"
            print(f"Base is missing from {pokemon_id}")
            pokemon['base'] = pokemon_base
            updated = True
        elif pokemon['base'] != pokemon_base:
            commit_title = f"Update base of `{pokemon_name.title()}`"
            print(f"Base is different in {pokemon_id}")
            pokemon['base'] = pokemon_base
            updated = True

        if updated:
            update_singularity_file(singularity_file, singularity)
            create_git_patch(commit_title, singularity_file, pokemon_source)
