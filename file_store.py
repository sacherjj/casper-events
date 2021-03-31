from typing import Union
from event_stream_reader import EventStreamReader
import config
from message_structure import MessageData
from pathlib import Path
from generate_finality_signatures import generate_finality_signatures_for_block
import json


esr = EventStreamReader(config.SSE_SERVER_URL)

# Three message types:
# DeployProcessed - Has no era_id, can store in block-hash folder and move into era_id folder when we get BlockAdded
#   Final location: era_<era_id>/<block_hash>/deploy-<deploy_hash>
# BlockAdded - Has era_id, can store in era_id folder
#   Final location: era_<era_id>/block-<block_hash>
# FinalitySignature = Has era_id, can store in era_id folder
#   Final location: era_<era_id>/<block_hash>/finsig-<block_hash>-<public_key>


def era_directory_name(era_id: Union[str,int]) -> str:
    return f"era_{era_id}"


def save_file_in_directory(directory: str, filename: str, contents: str, root_dir: Path = config.DATA_DIR):
    """ Creates directory if needed and saves file to filename in directory """
    target_dir = root_dir / directory
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / filename
    file_path.write_text(contents)


def move_deploys_to_era(directory: str, era_id: str, root_dir: Path = config.DATA_DIR):
    """ Moves all temp stored deploys into the proper era directory """
    source_dir = root_dir / directory
    target_dir = root_dir / era_directory_name(era_id) / directory
    if source_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        for src_file in source_dir.glob("deploy-*"):
            src_file.rename(target_dir / src_file.name)
        source_dir.rmdir()


def save_files():
    for msg in esr.messages():
        if not msg:
            continue
        data = MessageData(msg.data)
        era_id = data.era_id
        # We don't have a block for deploys yet as they process before the era_id is known.
        # Using a directory name in root data directory as block_hash
        directory = era_directory_name(era_id) if not data.is_deploy_processed else data.block_hash

        # We can go directly into a era/block_hash structure for finality_signatures
        if data.is_finality_signature:
            directory += f"/{data.block_hash}"
        # Deploys are made into block-<block_hash> directory that needs to be moved once BlockAdded test is what era the
        # Block was in.
        save_file_in_directory(directory, data.primary_key, msg.data)
        if data.is_block_added:
            # When a block is added, we know what the block era is for deploys stored, so we can copy them over.
            move_deploys_to_era(data.block_hash, era_id)


def get_era_directories(data_dir: Path = config.DATA_DIR):
    """ return era directory Paths in order of era """
    return sorted([era_dir for era_dir in data_dir.glob("era_*")], key=lambda d: int(str(d).split('era_')[-1]))


def get_block_hashes_from_dir(era_dir: Path):
    for block_file in era_dir.glob("block-*"):
        yield block_file.name.split("block-")[-1]


def is_missing_finsig_files(hash_dir: Path) -> bool:
    if not hash_dir.exists():
        return True
    return len(list(hash_dir.glob("finsig*"))) == 0


def recreate_finality_signatures(data_dir: Path = config.DATA_DIR):
    for era_dir in get_era_directories(data_dir):
        for hash in get_block_hashes_from_dir(era_dir):
            finsig_path = era_dir / hash
            if is_missing_finsig_files(finsig_path):
                try:
                    for finsig in generate_finality_signatures_for_block(hash):
                        data = MessageData(json.dumps(finsig))
                        save_file_in_directory(f"{era_dir.name}/{hash}", data.primary_key, finsig)
                        print(finsig)
                except Exception as e:
                    print(e)


save_files()
