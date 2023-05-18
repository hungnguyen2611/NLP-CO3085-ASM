class OpProceduralSemantic(object):
    def __init__(self, p_sems, op):
        self.p_sems = p_sems
        self.op = op

    def __str__(self):
        return self.op + ''.join([f'({p_sem.__str__()})' for p_sem in self.p_sems])


class ProceduralSemantic(object):
    def __init__(self, type=None, object=None, flight=None, start_place=None, end_place=None,
                 time=None):
        self.type = type
        self.object = object or ''
        if self.object == '?t1':
            self.object = ''
        self.flight = flight or ''
        self.start_place = start_place or ''
        self.end_place = end_place or ''
        self.time = time or ''
        if 'TIME' in self.type and self.time == '':
            self.time = '?t1'
        if self.time.endswith('giờ'):
            self.time = f"{self.time[:-4]}:00HR"

        if self.type == 'PRINT-ALL' and object == '?t1':
            self.object = '?t1'

    def __str__(self):
        return '{} {} {} {} {} {}'.format(self.type, self.object, self.flight, self.start_place,
                                          self.end_place,
                                          self.time)