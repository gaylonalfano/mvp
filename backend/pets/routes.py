# backend/pets/routes.py

from bson.objectid import ObjectId
from datetime import datetime
from config.config import DB, CONF
from fastapi import APIRouter, Depends, HTTPException
from starlette.status import HTTP_201_CREATED

import logging

from .models import PetBase, PetOnDB, PetsOut, PetKind, PetStatus


pets_router = APIRouter()


def validate_object_id(id_: str):
    try:
        _id = ObjectId(id_)
    except Exception:
        if CONF["fastapi"].get("debug", False):
            logging.warning("Invalid Object ID")
        raise HTTPException(status_code=400)
    return _id


async def _get_pet_or_404(id_: str):
    _id = validate_object_id(id_)
    pet = await DB.pet.find_one({"_id": _id})
    if pet:
        return fix_pet_id(pet)
    else:
        raise HTTPException(status_code=404, detail="Pet not found")


def fix_pet_id(pet):
    if pet.get("_id", False):
        pet["id_"] = str(pet["_id"])
        return pet
    else:
        raise ValueError(
            f"No `_id` found! Unable to fix pet ID for pet: {pet}"
        )


@pets_router.get(
    "/",
    response_model=PetsOut,
)
async def get_all_pets(
    kind: PetKind = None,
    status: PetStatus = None,
    limit: int = 10,
    skip: int = 0
):
    """[summary]
    Gets all pets.

    [description]
    Endpoint to retrieve pets.
    """
    if skip < 0:
        skip = 0
    if limit <= 0:
        limit = 10

    filter_db = {}
    if status and kind:
        filter_db = {"status": status.value, "kind": kind.value}
    elif status:
        filter_db = {"status": status.value}
    elif kind:
        filter_db = {"kind": kind.value}
    pets_cursor = DB.pet.find(filter_db)\
        .skip(skip)\
        .limit(limit)\
        .sort("created_at", -1)
    pets_count = await DB.pet.count_documents(filter_db)
    pets = await pets_cursor.to_list(length=limit)
    pets_list = list(map(fix_pet_id, pets))
    return {"pets": pets_list, "count": pets_count}


@pets_router.post("/", response_model=PetOnDB, status_code=HTTP_201_CREATED)
async def add_pet(pet: PetBase):
    """[summary]
    Inserts a new pet on the DB.

    [description]
    Endpoint to add a new pet.
    """
    date_now = datetime.utcnow().isoformat()
    pet_data = pet.dict()
    pet_data['last_modified'] = pet_data['created_at'] = date_now
    pet_op = await DB.pet.insert_one(pet_data)
    if pet_op.inserted_id:
        pet = await _get_pet_or_404(pet_op.inserted_id)
        pet["id_"] = str(pet["_id"])
        return pet


@pets_router.get(
    "/{id_}",
    response_model=PetOnDB
)
async def get_pet_by_id(id_: ObjectId = Depends(validate_object_id)):
    """[summary]
    Get one pet by ID.

    [description]
    Endpoint to retrieve an specific pet.
    """
    pet = await DB.pet.find_one({"_id": id_})
    if pet:
        pet["id_"] = str(pet["_id"])
        return pet
    else:
        raise HTTPException(status_code=404, detail="Pet not found")


@pets_router.delete(
    "/{id_}",
    dependencies=[Depends(_get_pet_or_404)],
    response_model=dict
)
async def delete_pet_by_id(id_: str):
    """[summary]
    Get one pet by ID.

    [description]
    Endpoint to retrieve an specific pet.
    """
    pet_op = await DB.pet.delete_one({"_id": ObjectId(id_)})
    if pet_op.deleted_count:
        return {"status": f"deleted count: {pet_op.deleted_count}"}


@pets_router.put(
    "/{id_}",
    dependencies=[Depends(validate_object_id), Depends(_get_pet_or_404)],
    response_model=PetOnDB
)
async def update_pet(id_: str, pet: PetBase):
    """[summary]
    Update a pet by ID.

    [description]
    Endpoint to update an specific pet with some or all fields.
    """
    pet_data = pet.dict()
    pet_data['last_modified'] = datetime.utcnow().isoformat()
    pet_op = await DB.pet.update_one(
        {"_id": ObjectId(id_)}, {"$set": pet_data}
    )
    if pet_op.modified_count:
        return await _get_pet_or_404(id_)
    else:
        raise HTTPException(status_code=304)
