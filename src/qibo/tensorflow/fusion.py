import functools
import operator
from qibo import K, gates
from qibo.base import fusion


class FusionGroup(fusion.FusionGroup):

    def __init__(self):
        super(FusionGroup, self).__init__()
        if K.custom_gates:
            from qibo import numpy as qnp
            self.K = qnp
        else:
            self.K = K

    def _one_qubit_matrix(self, gate0: "Gate", gate1: "Gate"):
        """Calculates Kroneker product of two one-qubit gates.

        Args:
            gate0: Gate that acts on ``self.qubit0``.
            gate1: Gate that acts on ``self.qubit1``.

        Returns:
            4x4 matrix that corresponds to the Kronecker product of the 2x2
            gate matrices.
        """
        if K.custom_gates:
            return self.K.kron(gate0.unitary, gate1.unitary)
        else:
            matrix = self.K.tensordot(gate0.unitary, gate1.unitary, axes=0)
            matrix = self.K.transpose(matrix, [0, 2, 1, 3])
            return self.K.reshape(matrix, (4, 4))

    def _two_qubit_matrix(self, gate: "Gate"):
        """Calculates the 4x4 unitary matrix of a two-qubit gate.

        Args:
            gate: Two-qubit gate acting on ``(self.qubit0, self.qubit1)``.

        Returns:
            4x4 unitary matrix corresponding to the gate.
        """
        matrix = gate.unitary
        if gate.qubits == (self.qubit1, self.qubit0):
            matrix = self.K.reshape(matrix, 4 * (2,))
            matrix = self.K.transpose(matrix, [1, 0, 3, 2])
            matrix = self.K.reshape(matrix, (4, 4))
        else:
            assert gate.qubits == (self.qubit0, self.qubit1)
        return matrix

    def _calculate(self):
        """Calculates the fused gate."""
        # Case 1: Special gate
        if self.special_gate is not None:
            assert not self.gates0[0] and not self.gates1[0]
            assert not self.two_qubit_gates
            return (self.special_gate,)

        # Case 2: Two-qubit gates only (no one-qubit gates)
        if self.first_gate(0) is None and self.first_gate(1) is None:
            assert self.two_qubit_gates
            # Case 2a: One two-qubit gate only
            if len(self.two_qubit_gates) == 1:
                return (self.two_qubit_gates[0],)

            # Case 2b: Two or more two-qubit gates
            fused_matrix = self._two_qubit_matrix(self.two_qubit_gates[0])
            for gate in self.two_qubit_gates[1:]:
                matrix = self._two_qubit_matrix(gate)
                fused_matrix = self.K.matmul(matrix, fused_matrix)
            return (gates.Unitary(fused_matrix, self.qubit0, self.qubit1),)

        # Case 3: One-qubit gates exist
        if not self.gates0[-1] and not self.gates1[-1]:
            self.gates0.pop()
            self.gates1.pop()

        # Fuse one-qubit gates
        ident0 = gates.I(self.qubit0)
        gates0 = (functools.reduce(operator.matmul, reversed(gates), ident0)
                  if len(gates) != 1 else gates[0] for gates in self.gates0)
        if self.qubit1 is not None:
            ident1 = gates.I(self.qubit1)
            gates1 = (functools.reduce(operator.matmul, reversed(gates), ident1)
                      if len(gates) != 1 else gates[0] for gates in self.gates1)

        # Case 3a: One-qubit gates only (no two-qubit gates)
        if not self.two_qubit_gates:
            gates0 = list(gates0)[::-1]
            fused_gate0 = (functools.reduce(operator.matmul, gates0, ident0)
                           if len(gates0) != 1 else gates0[0])
            if self.qubit1 is None:
                return (fused_gate0,)

            gates1 = list(gates1)[::-1]
            fused_gate1 = (functools.reduce(operator.matmul, gates1, ident1)
                           if len(gates1) != 1 else gates1[0])
            return (fused_gate0, fused_gate1)

        # Case 3b: One-qubit and two-qubit gates exist
        fused_matrix = self._one_qubit_matrix(next(gates0), next(gates1))
        for g0, g1, g2 in zip(gates0, gates1, self.two_qubit_gates):
            matrix = self._one_qubit_matrix(g0, g1)
            matrix2 = self._two_qubit_matrix(g2)
            fused_matrix = self.K.matmul(self.K.matmul(matrix, matrix2),
                                         fused_matrix)

        if len(self.two_qubit_gates) == len(self.gates0):
            g2 = self.two_qubit_gates[-1]
            if self.is_efficient(g2):
                fused_gate = gates.Unitary(fused_matrix, self.qubit0, self.qubit1)
                return (fused_gate, g2)

            matrix2 = self._two_qubit_matrix(g2)
            fused_matrix = self.K.matmul(matrix2, fused_matrix)

        fused_gate = gates.Unitary(fused_matrix, self.qubit0, self.qubit1)
        return (fused_gate,)
