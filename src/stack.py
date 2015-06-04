class ImmutableStack():
    def __init__(self, parent=None, element=None):
        self.parent = parent
        self.element = element

    def pop(self):
        assert self.parent is not None
        
        self.element = self.parent.element
        self.parent = self.parent.parent


    def push(self, element):
        node = ImmutableStack(self.parent, element)
        self.parent = node
        

    def listify(self):
        return self.parent.__listify([])[::-1]

    
    def __listify(self, output):
        output.append(self.element)

        if self.parent is None:
            return output
        
        return self.parent.__listify(output)
