from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

import zangar as z


@dataclass
class Node:
    name: str
    children: Union[List[Node], None] = None


def test():
    assert z.dataclass(Node).parse(
        {
            "name": "n1",
            "children": [
                {
                    "name": "n2",
                    "children": [
                        {"name": "n3"},
                    ],
                }
            ],
        }
    ) == Node(
        name="n1",
        children=[
            Node(
                name="n2",
                children=[
                    Node(name="n3"),
                ],
            )
        ],
    )
