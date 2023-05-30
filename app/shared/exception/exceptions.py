"""
@author: Kuro
"""


class PredicateConditionException(Exception):
    """
    Raising an exception for invalid predicate condition
    """

    doc = """
    There must be an explicit left hand condition for the predicate dictionary, I.E:\n
       {
            # one of these conditions must be met # 
            or_: [
            {
                # all of these conditions must be met #
                and_: {
                    key: value, ...
                    }, 
                    ...
                }
            ]   
            
            This allows for the chaining of scenarios such as:
            X and Y or Y and Z
            Y or X and Z and Y or Y and X
            etc...
                    """

    def __repr__(self):
        return self.doc

    def __str__(self):
        return self.doc

    def __doc__(self):
        return self.doc
