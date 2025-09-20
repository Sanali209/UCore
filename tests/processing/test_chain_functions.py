import pytest
from ucore_framework.core.processing.chain import DictFormatterChainFunction, DictFieldMergeChainFunction

def test_dict_formatter():
    formatter = DictFormatterChainFunction()
    formatter.mapping = {"full_name": ["first", "last"]}
    formatter.validators = {"full_name": lambda val: val.title()}
    result = formatter.run(first="john", last="doe")
    assert result == {"full_name": "John"}
    formatter.mapping = {"full_name": ["last", "first"]}
    result = formatter.run(first="john", last="doe")
    assert result == {"full_name": "Doe"}

def test_chained_execution():
    formatter = DictFormatterChainFunction()
    merger = DictFieldMergeChainFunction()
    formatter.mapping = {"name": ["input_name"]}
    merger.map = {"summary": ["name", "status"]}
    chain = formatter | merger
    result = chain.run(input_name="task_a", status="completed")
    assert result["name"] == "task_a"
    assert result["status"] == "completed"
    assert result["summary"] == "name=task_a|status=completed"
