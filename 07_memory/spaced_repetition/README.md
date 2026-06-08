# Spaced Repetition

Plain-Markdown flashcard decks using `due::` card metadata.

## Card Fields

- `due::` is the next review date in `YYYY-MM-DD`.
- `interval_days::` is the current review interval.
- `ease::` is a lightweight difficulty multiplier such as `2.30`.
- `state::` is `new`, `learning`, `review`, or `suspended`.

## Simple Rescheduling

- New card reviewed correctly: set `state:: review`, set `interval_days:: 1`, and set `due::` to tomorrow.
- Review card recalled correctly: multiply `interval_days::` by `ease::`, round to a whole day, keep `state:: review`, and move `due::` forward by that interval.
- Hard or missed card: set `state:: learning`, set `interval_days:: 1`, reduce `ease::` by about `0.15` without going below `1.30`, and set `due::` to tomorrow.
- Easy card: increase `ease::` by about `0.15` and move `due::` forward by the new interval.
- Suspended card: set `state:: suspended`; it can keep a far-future `due::` or no active due date.
