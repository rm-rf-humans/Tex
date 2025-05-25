# choosing gates in tikz circuits (latex)
from pylatex import TikZ, Command
from pylatex.tikz import TikZNode, TikZDraw, TikZPath

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
        self.position = position if position else [0, 0]
        self.inputs = inputs if inputs else "nn"

    def and_gate(self):
        return "and gate"
    
    def or_gate(self):
        return "or gate"
    
    def not_gate(self):
        return "not gate"
    
    def nand_gate(self):
        return "nand gate"
    
    def nor_gate(self):
        return "nor gate"
    
    def xor_gate(self):
        return "xor gate"
    
    def xnor_gate(self):
        return "xnor gate"

    def get_gate(self, gate_name):
        if gate_name.upper() in self.gates:
            gate_type = self.gates[gate_name.upper()]()
            return f"\\node[{gate_type}, draw, logic gate inputs = {self.inputs}] at ({self.position[1]}, {self.position[0]}) {{}};"
        else:
            raise ValueError(f"Gate '{gate_name}' is not defined.")
    
    def set_position(self, x, y):
        """Set the position of the gate"""
        self.position = [y, x]  # Note: TikZ uses (x,y) but we store as [y,x]
    
    def set_inputs(self, inputs):
        """Set the number of inputs for the gate"""
        self.inputs = inputs
    
    def get_tikz_code(self, gate_name, label=""):
        """Generate complete TikZ code for a gate with optional label"""
        gate_code = self.get_gate(gate_name)
        if label:
            # Add label to the gate
            gate_code = gate_code.replace("} {};", f"}} {{{label}}};")
        return gate_code
    
    def get_pylatex_node(self, gate_name, label="", node_name=""):
        """Generate PyLaTeX TikZNode for a gate"""
        if gate_name.upper() in self.gates:
            gate_type = self.gates[gate_name.upper()]()
            options = [gate_type, 'draw', f'logic gate inputs = {self.inputs}']
            
            node = TikZNode(
                text=label,
                at=f"({self.position[1]}, {self.position[0]})",
                options=options
            )
            
            if node_name:
                node.options.append(f"name={node_name}")
                
            return node
        else:
            raise ValueError(f"Gate '{gate_name}' is not defined.")
    
    def create_circuit_tikz(self, gates_list, connections=None):
        """Create a complete TikZ circuit using PyLaTeX"""
        tikz = TikZ(options=['circuit logic US'])
        
        # Add gates
        for gate_info in gates_list:
            gate_name = gate_info.get('type')
            position = gate_info.get('position', [0, 0])
            label = gate_info.get('label', '')
            node_name = gate_info.get('name', '')
            inputs = gate_info.get('inputs', self.inputs)
            
            self.set_position(position[0], position[1])
            self.set_inputs(inputs)
            
            node = self.get_pylatex_node(gate_name, label, node_name)
            tikz.append(node)
        
        # Add connections if provided
        if connections:
            for conn in connections:
                start = conn.get('from')
                end = conn.get('to')
                if start and end:
                    path = TikZDraw([start, '--', end])
                    tikz.append(path)
        
        return tikz
