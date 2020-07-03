import requests as r
from collections import defaultdict


class session():
    req = {"jsonrpc": "2.0", "id": 1}
    sid = None

    def __init__(self, server='http://raspisanie.admin.tomsk.ru/api/rpc.php'):
        self.server = server
        self.sid = self.request("startSession")['sid']

    def request(self, method, **params):
        if self.sid:
            params['sid'] = self.sid
        params['ok_id'] = ''

        body = dict(self.req, **{"method": method,  "params": params})
        ans = r.post(self.server, json=body).json()

        if 'result' in ans:
            return ans['result']
        elif 'error' in ans:
            raise Exception(ans['error'])
        else:
            raise Exception(ans)

    def search_stop(self, query):
        result = self.request('getStopsByName', str=query)
        stops = defaultdict(list)
        for e in result:
            e['st_id'] = [e['st_id']]
            stops[e['st_title']].append(e)

        for stop, obj in stops.items():
            info = obj[0]
            for e in obj[1:]:
                info['st_id'].append(e['st_id'][0])

            info.pop('st_lat')
            info.pop('st_long')

            stops[stop] = info

        return list(stops.values())

    def get_stop_arrivals(self, stop_id):
        return self.request('getStopArrive', st_id=stop_id)

    def get_stops_arrivals(self, stops_id):
        m = {}
        for stop_id in stops_id:
            for bus in self.get_stop_arrivals(stop_id):
                if not (bus['mr_num'], bus['rl_racetype']) in m:
                    m[(bus['mr_num'], bus['rl_racetype'])] = {'to': bus['laststation_title'],
                                                             'to_eng': bus['laststation_title_en'],
                                                             'units': [{'time': bus['tc_arrivetime'], 'inv': bool(int(bus['u_inv']))}]}
                else:
                    m[(bus['mr_num'], bus['rl_racetype'])]['units'].append({'time': bus['tc_arrivetime'], 'inv': bool(int(bus['u_inv']))})
        return m
