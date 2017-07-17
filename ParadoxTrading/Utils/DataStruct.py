import typing
from bisect import bisect_left, bisect_right
from datetime import datetime, timedelta

import h5py
import tabulate


class DataStruct:
    """

    the core data struct of ParadoxTrading

    :param _keys: the keys of this datastruct
    :param _index_name: the index of this datastruct
    :param _rows: init data, add as rows
    :param _dicts: init data, add as dicts

    """

    EXPAND_STRICT = 'strict'

    def __init__(
            self,
            _keys: typing.Sequence[str],
            _index_name: str,
            _rows: typing.Sequence = None,
            _dicts: typing.Sequence[dict] = None
    ):
        assert _index_name in _keys

        self.index_name = _index_name
        self.data: typing.Dict[str, typing.List] = {}
        for key in _keys:
            self.data[key] = []

        # this is the slice by index value
        self.loc: Loc = Loc(self)
        # this is the slice by number
        self.iloc: ILoc = ILoc(self)

        if _rows is not None:
            self.addRows(_rows, _keys)

        if _dicts is not None:
            self.addDicts(_dicts)

    def __getitem__(self, _item: str) -> typing.List[typing.Any]:
        """
        get one column of data

        :param _item: which column to pick
        :return: column of _item
        """
        assert type(_item) == str
        return self.data[_item]

    def __len__(self) -> int:
        """
        get the lenght of data

        :return: length
        """
        return len(self.index())

    def __iter__(self):
        """
        iter the row one by one
        """
        for i in range(len(self.index())):
            yield self.iloc[i]

    def __repr__(self):
        """
        print the data as a table by tabulate

        :return: the str of this table
        """
        if len(self) > 20:
            tmp_rows, tmp_keys = self.iloc[:8].toRows()
            tmp_rows.append(['...' for _ in tmp_keys])
            tmp_rows += self.iloc[-8:].toRows()[0]
            return tabulate.tabulate(tmp_rows, headers=tmp_keys)
        tmp_rows, tmp_keys = self.toRows()
        return tabulate.tabulate(tmp_rows, headers=tmp_keys)

    def clone(self, _columns: typing.List[str] = None) -> 'DataStruct':
        """
        copy all the data to a new datasturct,
        !!! WARN !!!: if the value in data is a reference to
        a object, it will just copy a reference to the same
        object

        :return: the new datastruct
        """
        if _columns is None:
            return self.iloc[:]

        keys_new = [self.index_name] + _columns
        datastruct = DataStruct(
            keys_new, self.index_name
        )
        keys_self = self.getColumnNames(_include_index_name=False)
        for column in _columns:
            assert column != self.index_name
            assert column in keys_self
        datastruct.addRows(*self.toRows(keys_new))
        return datastruct

    def merge(self, _struct: "DataStruct"):
        """
        merge one struct into self, and sorted by index

        :param _struct: another datastruct
        """
        self.addRows(*_struct.toRows())

    def expand(self, _struct: "DataStruct", _type: str = 'strict'):
        """
        expand columns by another datastruct
            - strict:
                1. two datastructs have the totally same index
                2. names in the other datastruct dont exist in self
                3. copy columns to self
            - ...

        :param _struct: another datastruct
        :param _type: expand type
        """
        if _type == self.EXPAND_STRICT:
            assert len(self) == len(_struct)
            for idx1, idx2 in zip(self.index(), _struct.index()):
                assert idx1 == idx2
            for name in _struct.getColumnNames(False):
                assert name not in self.getColumnNames()
            for name in _struct.getColumnNames(False):
                self.data[name] = _struct.getColumn(name)
        else:
            raise Exception('unknow type!')

    def addRow(
            self,
            _row: typing.Sequence[typing.Any],
            _keys: typing.Sequence[str]
    ):
        """
        add a row into self, the sort of row should be kept as keys

        :param _row: list of data to be added
        :param _keys: list of key
        """
        assert len(_row) == len(_keys)
        self.addDict(dict(zip(_keys, _row)))

    def addRows(
            self,
            _rows: typing.Sequence[typing.Sequence],
            _keys: typing.Sequence[str]
    ):
        """
        add mulit rows like addRow

        :param _rows:
        :param _keys:
        """
        for row in _rows:
            self.addRow(row, _keys)

    def addDict(self, _dict: typing.Dict[str, typing.Any]):
        """
        add dict into self

        :param _dict: map key to value
        :return:
        """
        index_value = _dict[self.index_name]
        insert_idx = bisect_right(self.index(), index_value)
        for k in self.data.keys():
            self.data[k].insert(insert_idx, _dict[k])

    def addDicts(self, _dicts: typing.Sequence[dict]):
        """
        add dicts into self, like addDict

        :param _dicts:
        :return:
        """
        for _dict in _dicts:
            self.addDict(_dict)

    def toRows(
            self, _keys=None
    ) -> (typing.Sequence[typing.Sequence[typing.Any]], typing.List[str]):
        """
        Turn data into rows, and the first return is the list of row,
        the second return is the keys.

        And you can set the keys to return by setting _keys,
        if not set, keys will be the whole keys in self.data

        :param _keys: the columns to return
        :return: rows and keys
        """
        rows = []
        keys: typing.List[str] = _keys
        if keys is None:
            keys = self.getColumnNames()
        for i in range(len(self)):
            rows.append([self.data[k][i] for k in keys])
        return rows, keys

    def toRow(
            self, _index: int = 0, _keys=None
    ) -> (typing.Sequence[typing.Any], typing.List[str]):
        """
        Turn one row into row, default it will turn the first line,
        _keys is the same as toRows

        :param _index:
        :param _keys:
        :return:
        """
        keys: typing.List[str] = _keys
        if keys is None:
            keys = self.getColumnNames()
        row = [self.data[k][_index] for k in keys]
        return row, keys

    def toDicts(self) -> (typing.List[typing.Dict[str, typing.Any]]):
        """
        turn all the data into dicts

        :return:
        """
        dicts = []
        rows, keys = self.toRows()
        for d in rows:
            dicts.append(dict(zip(keys, d)))
        return dicts

    def toDict(self, _index: int = 0) -> (typing.Dict[str, typing.Any]):
        """
        turn one row to the dict, default the first line

        :param _index:
        :return:
        """
        row, keys = self.toRow(_index)
        return dict(zip(keys, row))

    def toHDF5(self, _f_name: str, _mode: str = 'w'):
        """
        save data struct to hdf5

        :param _f_name:
        :param _mode:
        :return:
        """
        f = h5py.File(_f_name, _mode)
        f.attrs['index_name'] = self.index_name

        for k, v in self.data.items():
            v_sample = v[0]
            if isinstance(v_sample, int):
                dtype = 'int32'
                attr = 'int'
            elif isinstance(v_sample, float):
                dtype = 'float64'
                attr = 'float'
            elif isinstance(v_sample, str):
                dtype = h5py.special_dtype(vlen=str)
                attr = 'str'
            elif isinstance(v_sample, datetime):
                dtype = 'float64'
                attr = 'datetime'
            else:
                raise Exception('unsupported type, sorry')

            if attr == 'datetime':
                self.datetime2float(k)

            dataset = f.create_dataset(
                k, (len(self),), dtype=dtype
            )
            dataset[:] = self[k]
            dataset.attrs['type'] = attr

            if attr == 'datetime':
                self.float2datetime(k)

        f.close()

    @staticmethod
    def fromHDF5(_f_name: str) -> 'DataStruct':
        """
        load data struct from hdf5

        :param _f_name:
        :return:
        """
        f = h5py.File(_f_name)

        datastruct = DataStruct(list(f.keys()), f.attrs['index_name'])
        for k in f.keys():
            dataset = f[k]
            datastruct.data[k] = dataset[:].tolist()
            if dataset.attrs['type'] == 'datetime':
                datastruct.float2datetime(k)

        f.close()
        return datastruct

    def index(self) -> list:
        """
        return the column of index

        :return:
        """
        return self.data[self.index_name]

    def getColumnNames(
            self, _include_index_name: bool = True
    ) -> typing.Sequence[str]:
        """
        return sorted keys, if _include_index_name is False,
        return sorted keys but index_name

        :param _include_index_name:
        :return:
        """
        if _include_index_name:
            return sorted(self.data.keys())
        else:
            tmp = {self.index_name}
            return sorted(self.data.keys() - tmp)

    def changeIndex(self, _new_index: str) -> 'DataStruct':
        """
        change index_name, and return a new datastruct with index changed

        :param _new_index:
        :return:
        """
        assert _new_index in self.data.keys()
        tmp = DataStruct(self.getColumnNames(), _new_index)
        tmp.merge(self)
        return tmp

    def changeColumnName(self, _old_name: str, _new_name: str):
        """
        change column name

        :param _old_name:
        :param _new_name:
        :return:
        """
        assert _old_name != _new_name
        if self.index_name == _old_name:
            self.index_name = _new_name
        self.data[_new_name] = self.data[_old_name]
        del self.data[_old_name]

    def getColumn(self, _key: str) -> list:
        """
        return one column by key

        :param _key:
        :return:
        """
        return self.data[_key]

    def dropColumn(self, _key: str):
        """
        del one column

        :param _key:
        :return:
        """
        assert _key != self.index_name
        assert _key in self.data.keys()
        del self.data[_key]

    def createColumn(self, _key: str, _column: typing.Sequence[typing.Any]):
        """
        add one column into self, check the len of new column,
        !!! WARN !!! you should keep the sort by yourself

        :param _key:
        :param _column:
        :return:
        """
        assert _key not in self.data.keys()
        assert len(_column) == len(self)
        self.data[_key] = _column

    def any2str(self, _key: str = None):
        """
        turn one column from any typing to str, simply use str()

        :param _key: default use index
        :return:
        """
        k = _key
        if k is None:
            k = self.index_name
        self.data[k] = [str(d) for d in self.data[k]]

    def datetime2float(self, _key: str = None):
        """
        turn one column from datetime to float

        :param _key:
        :return:
        """
        k = _key
        if k is None:
            k = self.index_name
        self.data[k] = [(d - datetime(1970, 1, 1)).total_seconds()
                        for d in self.data[k]]

    def float2datetime(self, _key: str = None):
        """
        turn float back to datetime

        :param _key:
        :return:
        """
        k = _key
        if k is None:
            k = self.index_name
        self.data[k] = [datetime(1970, 1, 1) + timedelta(seconds=d)
                        for d in self.data[k]]

    def str2float(self, _key: str = None):
        """
        turn one column from str to float, simply use float()

        :param _key:
        :return:
        """
        k = _key
        if k is None:
            k = self.index_name
        self.data[k] = [float(d) for d in self.data[k]]

    def str2int(self, _key: str = None):
        """
        turn one column from str to int, simply use int()

        :param _key:
        :return:
        """
        k = _key
        if k is None:
            k = self.index_name
        self.data[k] = [int(d) for d in self.data[k]]

    def str2datetime(self, _key: str = None):
        """
        turn one column from str to datetime

        :param _key:
        :return:
        """
        k = _key
        if k is None:
            k = self.index_name
        self.data[k] = [datetime.strptime(d, '%Y%m%d %H:%M:%S.%f')
                        for d in self.data[k]]


class Loc:
    def __init__(self, _struct: DataStruct):
        self.struct = _struct

    def __getitem__(self, _item: typing.Union[typing.Any, slice]):
        """
        if getitem by the index value, return the result if index value found
        else return None,

        if getitem by a range of index value, return the range of values by find
        the number of start and stop, (start is included, stop excluded)

        :param _item:
        :return:
        """
        if isinstance(_item, slice):
            new_start = None
            if _item.start is not None:
                new_start = bisect_left(self.struct.index(), _item.start)
            new_stop = None
            if _item.stop is not None:
                new_stop = bisect_left(self.struct.index(), _item.stop)
            new_item = slice(new_start, new_stop)
            return self.struct.iloc.__getitem__(new_item)
        else:
            n_i = bisect_left(self.struct.index(), _item)
            if n_i != len(self.struct) and _item == self.struct.index()[n_i]:
                return self.struct.iloc.__getitem__(n_i)
            else:
                return None


class ILoc:
    def __init__(self, _struct: DataStruct):
        self.struct = _struct

    def __getitem__(self, _item: typing.Union[int, slice]) -> DataStruct:
        """
        create a new datastruct according to self,
        and add the data according to _item

        :param _item:
        :return:
        """
        ret = DataStruct(self.struct.getColumnNames(), self.struct.index_name)
        if isinstance(_item, slice):
            for k, v in self.struct.data.items():
                ret.data[k] = v.__getitem__(_item)
        else:
            for k, v in self.struct.data.items():
                ret.data[k] = [v[_item]]
        return ret
