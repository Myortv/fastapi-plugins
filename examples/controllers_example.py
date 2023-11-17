from plugins.controllers import (
    insert_q,
    delete_q,
    update_q,
    select_q,
)

from pydantic import BaseModel


class TestModel(BaseModel):
    id: int
    body: str
    some_value: int


test_data = TestModel(
    id=1,
    body="Some testing body data",
    some_value=100,
)

# print(result[0])
# print(*insert_q(test_data, 'testing_datatable'))
# print() 
# result = insert_q(test_data, 'testing_datatable')

# # print(*insert_q(test_data, 'testing_datatable', result[0], result[1:]))

with_statement = (
    "with other_table as (\n"
        "\tselect * from another_one_table\n"
        "\twhere id = $1 and name = $2\n"
    ")\n"
)

with_arguments = (
    5, "nice_name"
)


# print(*insert_q(test_data, 'testing_datatable', with_statement, with_arguments))
print(*select_q('datatable', id=1, b=2))
