# choosing gates in tikz circuits (latex)
class Gates:
    def __init__(self, position=[], gate_name=None, inputs=None):
        self.gates = {
            "AND": self.and_gate,
            "OR": self.or_gate,
            "NOT": self.not_gate,
            "NAND": self.nand_gate,
            "NOR": self.nor_gate,
            "XOR": self.xor_gate,
            "XNOR": self.xnor_gate
        }
        self.position = position 

        self.inputs = inputs

    def get_gate(self, gate_name):
        if gate_name in self.gates:
            return f"\node[{self.gates[gate_name.lower()]}, draw, logic gate inputs = {self.inputs} ] at ({self.position[-1]}, {self.position[0]}) {{}};"
        else:
            raise ValueError(f"Gate '{gate_name}' is not defined.")
