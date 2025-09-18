"""
Composable Chain-of-Responsibility and Data Processing Utilities for UCore

This module provides a flexible, functional pipeline abstraction for chaining data processing steps.
Classes:
    - ChainFunction: Base class for composable, chainable operations.
    - PrintToChainFunction: Prints a message as part of a chain.
    - DictFormatterChainFunction: Formats dictionary fields according to mapping and validators.
    - DictFieldMergeChainFunction: Merges multiple fields into one.

Example usage:
    from framework.processing.chain import DictFormatterChainFunction, PrintToChainFunction

    formatter = DictFormatterChainFunction()
    formatter.mapping = {"full_name": ["first_name", "last_name"]}
    formatter.validators = {"full_name": lambda val: val.title()}

    printer = PrintToChainFunction()
    chain = formatter | printer

    chain.run(first_name="john", last_name="doe")
    # Output: John Doe
"""

from typing import Callable, Dict, Any, Optional

class ChainFunction:
    """
    Base class for composable, chainable operations.
    """
    def __init__(self):
        self.next_f: Optional["ChainFunction"] = None
        self.operation: Optional[Callable] = None
        self.in_dict: Dict[str, Any] = {}
        self.pass_truth_in_dict = False

    def set_last(self, last_f: "ChainFunction"):
        if self.next_f is not None:
            self.next_f.set_last(last_f)
        else:
            self.next_f = last_f

    def __or__(self, other: "ChainFunction"):
        self.set_last(other)
        return self

    def execute_operation(self):
        if self.operation is not None:
            return self.operation(**self.in_dict)
        return self.in_dict

    def run(self, **kwargs):
        self.in_dict = {**kwargs}
        result = self.execute_operation()
        if self.next_f is not None:
            return self.next_f.run(**result)
        return result

class PrintToChainFunction(ChainFunction):
    """
    ChainFunction that prints a message and passes a response.
    """
    def __init__(self):
        super().__init__()

        def printTest(message):
            print(message)
            return {'response': 'ok'}

        self.operation = printTest

    def run(self, message="", **kwargs):
        kwargs["message"] = message
        return super().run(**kwargs)

class DictFormatterChainFunction(ChainFunction):
    """
    Formats dictionary fields according to mapping and validators.

    Example:
        format = DictFormatterChainFunction()
        format.mapping = {"target_field": ["field1", "field2"]}
        format.validators = {"target_field": lambda val: val}
    """
    def __init__(self):
        super().__init__()
        self.mapping: Dict[str, list] = {}
        self.validators: Dict[str, Callable] = {}
        self.copy_source = False
        self.verbose = True
        self.operation = self.format

    def format(self, **kwargs):
        ret_dict: dict = {}
        if self.copy_source:
            ret_dict = {**kwargs}
        for dest_key in self.mapping.keys():
            if dest_key not in ret_dict:
                source_keys = self.mapping[dest_key]
                for s_key in source_keys:
                    if s_key in kwargs:
                        validator = self.validators.get(dest_key, lambda val: val)
                        val = validator(kwargs[s_key])
                        ret_dict[dest_key] = val
                        break
        return ret_dict

class DictFieldMergeChainFunction(ChainFunction):
    """
    Merges fields from input dictionary into one field.

    Example:
        merge = DictFieldMergeChainFunction()
        merge.map = {"target_field": ["field1", "field2"]}
    """
    def __init__(self):
        super().__init__()
        self.map: Dict[str, list] = {}
        self.pass_truth_dict = True
        self.operation = self.collect
        self.verbose = False
        self.splitter: str = "|"
        self.include_source_name = True

    def collect(self, **kwargs):
        ret_dict = {}
        if self.pass_truth_dict:
            ret_dict = {**kwargs}
        for key in self.map:
            summary_str = []
            fields = self.map[key]
            for field in fields:
                if field in kwargs:
                    if self.include_source_name:
                        summary_str.append(f"{field}={str(kwargs[field])}")
                    else:
                        summary_str.append(str(kwargs[field]))
                    ret_dict[key] = self.splitter.join(summary_str)
        return ret_dict
