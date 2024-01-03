from objects import *


def chain(objs):
    for i in range(len(objs) - 1):
        objs[i].output = objs[i + 1]
        objs[i + 1].input = objs[i]


def init(t_k1=3, mu_k2=0.25, t_k3=4, capacity_q2=5):
    """

    :param t_k1: time for K1 to process a customer
    :param mu_k2: mu for K2 to process a customer
    :param t_k3: time for K3 to process a customer
    :param capacity_q2: K2 queue capacity
    :return:
    """
    em = EventManager()

    input_plug = Line(event_manager=em, name='input plug')
    input_plug.output_unblocked_reaction = lambda: ...

    l1 = Line(event_manager=em, name='L1')
    l2 = Line(event_manager=em, name='L2')
    l3 = Line(event_manager=em, name='L3')
    l4 = Line(event_manager=em, name='L4')

    k1 = K(event_manager=em, t=t_k1, name='K1')

    q2 = Q(event_manager=em, capacity=capacity_q2, name='[Q of K2]')
    k2 = K(event_manager=em, mu=mu_k2, name='K2')

    k3 = K(event_manager=em, t=t_k3, name='K3')
    exit = Exit(event_manager=em)

    chain([input_plug, l1, k1, l2, q2, k2, l3, k3, l4, exit])

    return em, l1


def simulate(em: EventManager, l1: Line, la=0.2, n=8):
    """

    :param em:
    :param l1:
    :param la: lambda for customer arrivals
    :param n: n customers to simulate
    :return: (rejection_rate, avg_wait_time, avg_q_len)
    """

    mean = 1 / la

    customers = np.cumsum(npr.exponential(mean, size=n))
    for c in customers:
        em.add_event(c, l1.move, name='new customer at L1')
    em.events = sorted(em.events, key=lambda x: x.time)

    while em.events:
        ne = em.get_next_event()
        try:
            ne.action()
        except Exception as e:
            print("!***", ne)
            raise e

    ce = [e for e in em.log if e['type'] == 'customer_exit']
    rej = [e for e in em.log if e['type'] == 'rejection']
    rejection_rate = len(rej) / (len(ce) + len(rej))

    ql = [e['length'] for e in em.log if e['type'] == 'queue length']
    qt = [e['time'] for e in em.log if e['type'] == 'queue length']

    max_time = max([e['time'] for e in em.log])
    qt.append(max_time)
    qt = np.diff(qt)

    avg_q_len = 0
    avg_wait_time = 0
    if len(ql) > 0:
        avg_q_len = sum(np.array(ql) * np.array(qt)) / max_time

        wt = [e['wait_time'] for e in em.log if e['type'] == 'queue remove']
        # avg_wait_time = sum(wt) / len(wt)
        avg_wait_time = sum(wt) / len(ce)

    return (rejection_rate, avg_wait_time, avg_q_len)


def simulate_n_times(n_sim=10, **kwargs):
    results = []
    for i in range(n_sim):
        results.append(simulate(**kwargs))

    return (np.mean([r[0] for r in results]),
            np.mean([r[1] for r in results]),
            np.mean([r[2] for r in results]))


if __name__ == '__main__':
    em, l1 = init()
    print(simulate_n_times(n_sim=100, em=em, l1=l1, la=0.2, n=8))
