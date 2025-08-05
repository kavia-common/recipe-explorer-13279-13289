from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel, Field
# --- Swagger Tags Metadata ---
openapi_tags = [
    {
        "name": "Recipes",
        "description": "Operations related to discovering, searching, and retrieving recipes."
    },
    {
        "name": "Collections",
        "description": "Operations for managing user's saved/favorite collections."
    },
    {
        "name": "Categories",
        "description": "Recipe category browsing endpoints."
    },
]

app = FastAPI(
    title="Recipe Explorer Backend",
    description="Backend API for searching, viewing, and managing recipes and user collections for Recipe Explorer.",
    version="1.0.0",
    openapi_tags=openapi_tags
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict origins.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dummy Data Structures ---

# Dummy Recipe DB
DUMMY_RECIPES = [
    {
        "id": "1",
        "title": "Classic Pancakes",
        "category": "Breakfast",
        "ingredients": [
            {"name": "Flour", "amount": "2 cups"},
            {"name": "Eggs", "amount": "2"},
            {"name": "Milk", "amount": "1.5 cups"},
            {"name": "Baking Powder", "amount": "2 tsp"},
            {"name": "Salt", "amount": "0.5 tsp"}
        ],
        "instructions": [
            "Mix flour, baking powder, and salt.",
            "Add eggs and milk, whisk until smooth.",
            "Pour batter onto hot griddle, cook until bubbles form, then flip.",
            "Serve warm with syrup."
        ],
        "description": "Fluffy, easy pancakes perfect for any morning."
    },
    {
        "id": "2",
        "title": "Spaghetti Bolognese",
        "category": "Dinner",
        "ingredients": [
            {"name": "Spaghetti", "amount": "200g"},
            {"name": "Ground Beef", "amount": "250g"},
            {"name": "Tomato Sauce", "amount": "1 cup"},
            {"name": "Onion", "amount": "1, chopped"},
            {"name": "Garlic", "amount": "2 cloves, minced"},
        ],
        "instructions": [
            "Cook spaghetti according to package instructions.",
            "Brown beef in a pan, add onion and garlic, cook until soft.",
            "Add tomato sauce and simmer.",
            "Serve sauce over spaghetti."
        ],
        "description": "A hearty Italian classic with rich tomato and beef sauce."
    },
    {
        "id": "3",
        "title": "Cheese Omelette",
        "category": "Breakfast",
        "ingredients": [
            {"name": "Eggs", "amount": "3"},
            {"name": "Cheese", "amount": "50g, grated"},
            {"name": "Butter", "amount": "1 tbsp"},
            {"name": "Salt", "amount": "to taste"},
            {"name": "Pepper", "amount": "to taste"}
        ],
        "instructions": [
            "Beat eggs with salt and pepper.",
            "Melt butter in a pan.",
            "Pour eggs into pan, cook 1-2 min, sprinkle cheese over.",
            "Fold omelette and serve warm."
        ],
        "description": "Quick, protein-packed, and melty cheese for breakfast."
    }
]

# Dummy categories
DUMMY_CATEGORIES = ["Breakfast", "Lunch", "Dinner", "Desserts", "Snacks", "Vegan"]

# Dummy user "favorites" collection in-memory store (by "user id")
DUMMY_USER_COLLECTIONS = {
    "demo-user": {"1"}  # Set of recipe IDs
}

# --- MODELS ---

class Ingredient(BaseModel):
    name: str = Field(..., description="Name of the ingredient")
    amount: str = Field(..., description="Amount/measurement for the ingredient")

class Instruction(BaseModel):
    step: int = Field(..., description="Step number")
    description: str = Field(..., description="Instruction details")

class RecipeSummary(BaseModel):
    id: str = Field(..., description="Recipe unique identifier")
    title: str = Field(..., description="Recipe title")
    category: str = Field(..., description="Recipe category")
    description: Optional[str] = Field(None, description="Recipe short description")

class RecipeDetail(BaseModel):
    id: str
    title: str
    category: str
    description: Optional[str]
    ingredients: List[Ingredient]
    instructions: List[str]

class Category(BaseModel):
    name: str

class CollectionUpdate(BaseModel):
    recipe_id: str

class CollectionResponse(BaseModel):
    user_id: str
    collections: List[RecipeSummary]

# --- UTILITY ---

def _search_recipes(query: Optional[str], category: Optional[str]):
    """Simple search with query and optional category."""
    filtered = DUMMY_RECIPES
    if query:
        filtered = [r for r in filtered if query.lower() in r["title"].lower()]
    if category:
        filtered = [r for r in filtered if r["category"].lower() == category.lower()]
    return filtered


def _get_recipe(recipe_id: str):
    return next((r for r in DUMMY_RECIPES if r["id"] == recipe_id), None)

def _get_user_favorites(user_id: str):
    return DUMMY_USER_COLLECTIONS.get(user_id, set())

# --- API ENDPOINTS ---

# PUBLIC_INTERFACE
@app.get("/", tags=["Recipes"])
def health_check():
    """
    Simple health check for API availability.
    """
    return {"message": "Healthy"}

# PUBLIC_INTERFACE
@app.get("/recipes", response_model=List[RecipeSummary], tags=["Recipes"], summary="List/search recipes", description="Get a list of recipes, optionally filtered by search query or category.")
def list_recipes(
    q: Optional[str] = Query(None, description="Search term for recipe title"),
    category: Optional[str] = Query(None, description="Category name to filter recipes")
):
    """
    Retrieve a list of available recipes. Supports optional search by title substring and filtering by category.
    """
    data = _search_recipes(q, category)
    output = [
        RecipeSummary(
            id=r["id"],
            title=r["title"],
            category=r["category"],
            description=r.get("description", "")
        )
        for r in data
    ]
    return output

# PUBLIC_INTERFACE
@app.get("/recipes/{recipe_id}", response_model=RecipeDetail, tags=["Recipes"], summary="Recipe details", description="Get all details for a single recipe including ingredients and instructions.")
def get_recipe_details(
    recipe_id: str = Path(..., description="ID of the recipe to fetch")
):
    """
    Retrieve detailed information about a recipe.
    """
    recipe = _get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return RecipeDetail(
        id=recipe["id"],
        title=recipe["title"],
        category=recipe["category"],
        description=recipe.get("description", ""),
        ingredients=[Ingredient(**ing) for ing in recipe["ingredients"]],
        instructions=recipe["instructions"]
    )

# PUBLIC_INTERFACE
@app.get("/categories", response_model=List[Category], tags=["Categories"], summary="List categories", description="Get all available recipe categories.")
def list_categories():
    """
    Retrieve a list of all recipe categories for browsing.
    """
    return [Category(name=c) for c in DUMMY_CATEGORIES]

# PUBLIC_INTERFACE
@app.get("/categories/{category}", response_model=List[RecipeSummary], tags=["Categories"], summary="Browse recipes by category", description="Get recipes under a given category.")
def browse_by_category(
    category: str = Path(..., description="Category to filter recipes")
):
    """
    Get recipes that belong to a specified category.
    """
    recipes = [r for r in DUMMY_RECIPES if r["category"].lower() == category.lower()]
    return [
        RecipeSummary(
            id=r["id"],
            title=r["title"],
            category=r["category"],
            description=r.get("description", "")
        )
        for r in recipes
    ]

# PUBLIC_INTERFACE
@app.get("/users/{user_id}/collections", response_model=CollectionResponse, tags=["Collections"], summary="Get user recipe collection", description="Get all recipes saved/favorited by a user.")
def get_user_collection(
    user_id: str = Path(..., description="User ID whose collection to retrieve")
):
    """
    Get all favorited/saved recipes for the specified user.
    """
    recipe_ids = _get_user_favorites(user_id)
    recipes = [r for r in DUMMY_RECIPES if r["id"] in recipe_ids]
    return CollectionResponse(
        user_id=user_id,
        collections=[
            RecipeSummary(
                id=r["id"],
                title=r["title"],
                category=r["category"],
                description=r.get("description", "")
            ) for r in recipes
        ]
    )

# PUBLIC_INTERFACE
@app.post("/users/{user_id}/collections", response_model=CollectionResponse, tags=["Collections"], summary="Add recipe to collection", description="Add a recipe to the user's collection.")
def add_user_collection(
    user_id: str = Path(..., description="User ID"),
    update: CollectionUpdate = None
):
    """
    Add a recipe to the user's favorites/collection.
    """
    if update is None or not update.recipe_id:
        raise HTTPException(status_code=400, detail="Missing recipe_id")
    recipe = _get_recipe(update.recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    DUMMY_USER_COLLECTIONS.setdefault(user_id, set()).add(update.recipe_id)
    # Return updated collection
    return get_user_collection(user_id)

# PUBLIC_INTERFACE
@app.delete("/users/{user_id}/collections/{recipe_id}", response_model=CollectionResponse, tags=["Collections"], summary="Remove recipe from collection", description="Remove a recipe from the user's collection.")
def remove_user_collection(
    user_id: str = Path(..., description="User ID"),
    recipe_id: str = Path(..., description="Recipe ID to remove from favorites")
):
    """
    Remove a recipe from the user's favorites/collection.
    """
    if user_id in DUMMY_USER_COLLECTIONS:
        DUMMY_USER_COLLECTIONS[user_id].discard(recipe_id)
    return get_user_collection(user_id)

# PUBLIC_INTERFACE
@app.get("/recipes/{recipe_id}/ingredients", response_model=List[Ingredient], tags=["Recipes"], summary="Get ingredients for a recipe", description="Fetch the ingredient list for a given recipe.")
def get_ingredients(
    recipe_id: str = Path(..., description="Recipe ID")
):
    """
    Get the list of ingredients for a specified recipe.
    """
    recipe = _get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return [Ingredient(**ing) for ing in recipe["ingredients"]]

# PUBLIC_INTERFACE
@app.get("/recipes/{recipe_id}/instructions", response_model=List[str], tags=["Recipes"], summary="Get instructions for a recipe", description="Fetch the instructions for a given recipe.")
def get_instructions(
    recipe_id: str = Path(..., description="Recipe ID")
):
    """
    Get the step-by-step instructions for a specified recipe.
    """
    recipe = _get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe["instructions"]

