import sys
import json

import pydent
from pydent import AqSession

class Navigator():

    def __init__(self, config_path='./', instance='nursery'):
        self.set_session(config_path, instance)

    def set_session(self, config_path, instance):
        """
        Creates a session to be used by the Navigator.

        Arguments:
        config_path (string): path to a json file that has valid credentials
        instance (string): specifies which Aq instance to use
        """
        with open('secrets.json') as f:
            secrets = json.load(f)

        credentials = secrets[instance]
        session = AqSession(
            credentials["login"],
            credentials["password"],
            credentials["aquarium_url"]
        )

        # Test the session
        me = session.User.where({'login': credentials['login']})[0]
        print('Logged in as %s\n' % me.name)

        self.session = session

    def output_fvs(self, item_id):
        """
        Returns output FieldValues for a given Item id.

        Arguments:
        item_id (int): id of an Item
        """
        return self.session.FieldValue.where({'role': 'output', 'child_item_id': item_id})

    def input_fvs(self, item_id):
        """
        Returns input FieldValues for a given Item id.

        Arguments:
        item_id (int): id of an Item
        """
        return self.session.FieldValue.where({'role': 'input', 'child_item_id': item_id})

    def predecessor_ops(self, item_id):
        """
        Returns Operations for which a given Item is an output.

        Arguments:
        item_id (int): id of an Item
        """
        fvs = self.output_fvs(item_id)
        return [fv.operation for fv in fvs]

    def successor_ops(self, item_id):
        """
        Returns Operations for which a given Item is an input.

        Arguments:
        item_id (int): id of an Item
        """
        fvs = self.input_fvs(item_id)
        return [fv.operation for fv in fvs]

    def walk_back(self, stop_at, item_id, row=None, col=None, ops=None):
        """
        Recursively finds the Operation backchain for a given item.
        Goes back to a specified OperationType, then stops.
        Returns a list of Operations.

        Arguments:
        stop_at (string): name of the OperationType of the Operation to stop at
        item_id (int): id of an Item
        row (string): the row location if the Item is a collection
        column (string): the column location if the Item is a collection
        ops (list): the list of operations to be returned
        """
        if ops is None:
            ops = []

        pred_fvs = self.output_fvs(item_id)
        pred_fvs = [fv for fv in pred_fvs if fv.row == row and fv.column == col]

        if not pred_fvs:
            return ops

        op_ids = [op.id for op in ops]
        pred_ops = [fv.operation for fv in pred_fvs if fv.operation.id not in op_ids]
        pred_ops = sorted(pred_ops, key=lambda op: self.job_completed(op))
        pred_op = pred_ops[-1]

        print(str(pred_op.id) + " " + pred_op.operation_type.name)

        ops.append(pred_op)

        if pred_op.operation_type.name == stop_at:
            return ops

        try:
            input_fv = self.get_input_fv(pred_op, item_id)

        except InputNotFoundError as e:
            print(e.args[0])
            return ops

        return self.walk_back(stop_at, input_fv.child_item_id, input_fv.row, input_fv.column, ops)

    @staticmethod
    def job_completed(op):
        """
        Returns the completion date for the most recent Job for a given Operation.

        Arguments:
        op (Operation)
        """
        jobs = sorted(op.jobs, key=lambda job: job.updated_at)
        return jobs[-1].updated_at

    def get_input_fv(self, op, output_item_id):
        """
        Returns the most likely input FieldValue for a given Operation and output Item.

        Arguments:
        op (Operation): the Operation to search within
        output_item_id (int): the id of the output Item
        """
        """If only one input, then the answer is obvious"""
        inputs = op.inputs
        if len(inputs) == 1:
            return inputs[0]

        """If more than one input, then it attempts to use routing"""
        routing_matches = self.get_routing_matches(op, output_item_id)
        if routing_matches:
            return routing_matches[0]

        """If no routing (bad developer!) then it attempts to match Sample name"""
        sample_name_matches = self.get_sample_name_matches(op, output_item_id)
        if sample_name_matches:
            return sample_name_matches[0]

        """Gives up"""
        raise InputNotFoundError(
            "No input for output item %d in operation %d." % (output_item_id, op.id)
        )

    def get_routing_matches(self, op, output_item_id):
        """
        Returns input FieldValues for the given Operation with the same routing as the given output Item

        Arguments:
        op (Operation)
        output_item_id (int)
        """
        fvs = self.session.FieldValue.where({
            'role': 'output',
            'parent_id': op.id,
            'parent_class': 'Operation',
            'child_item_id': output_item_id
        })

        fv = fvs[-1]
        return [i for i in op.inputs if i.field_type and i.field_type.routing == fv.field_type.routing]

    def get_sample_name_matches(self, op, output_item_id):
        """
        Returns input FieldValues for the given Operation with the same Sample name as the given output Item

        Arguments:
        op (Operation)
        output_item_id (int)
        """
        sn = self.session.Item.find(output_item_id).sample.name
        return [i for i in op.inputs if i.sample and i.sample.name == sn]

    def plan_outputs(self, plan_id, operation_type_name, output_name):
        """
        Returns output Items for a Plan given by the plan_id, operation_type_name, and output_name

        Arguments:
        plan_id (int)
        operation_type_name (str)
        output_name (str)
        """
        if isinstance(plan_id, int):
            plan_id = [plan_id]

        outputs = []

        for p in plan_id:
            plan = self.session.Plan.find(p)
            ops = plan.operations
            ops = [op for op in ops if op.operation_type.name == operation_type_name]
            fvs = [op.output(output_name) for op in ops]
            outputs += [fv.item.id for fv in fvs if fv.item]

        return outputs


class InputNotFoundError(Exception):
    """Trident could not find an input for this operation"""


class NoPredecessorsError(Exception):
    """No predecessor was found where one was expected"""
