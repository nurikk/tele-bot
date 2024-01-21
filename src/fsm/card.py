from aiogram.fsm.state import StatesGroup, State


class CardForm(StatesGroup):
    reason = State()  # What's the reason of postcard? (merry Christmas, birthday, etc.)
    relationship = (
        State()
    )  # What is your relationship with the person being congratulated?

    description = State()  # Describe the person being congratulated.

    depiction = State()  # What would you like to depict on a postcard?
    # (photo, drawing, collage, etc.)
    style = State()  # Choose the postcard style.
