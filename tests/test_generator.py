import builtins
import io
import os
import sys

import pytest
from unittest.mock import patch

sys.path.insert(0, os.getcwd())
from cimrdfpy import generator


@pytest.fixture(scope='module')
def delete_generated_files(monkeypatch):
    def patch_open(open_func, files):
        def open_patched(path,
                         mode='r',
                         buffering=-1,
                         encoding=None,
                         errors=None,
                         newline=None,
                         closefd=True,
                         opener=None):
            if 'w' in mode and not os.path.isfile(path):
                files.append(path)
            return open_func(path,
                             mode=mode,
                             buffering=buffering,
                             encoding=encoding,
                             errors=errors,
                             newline=newline,
                             closefd=closefd,
                             opener=opener)

        return open_patched

    files = []
    monkeypatch.setattr(builtins, 'open', patch_open(builtins.open, files))
    monkeypatch.setattr(io, 'open', patch_open(io.open, files))
    yield
    for file in files:
        os.remove(file)


def test_output_generation():
    with patch.object(sys, 'argv', ['', './tests/test_rdfs.xml', './tests/output.py']):
        generator.main()


def test_raises_validation_error():
    from tests.output import Switch
    with pytest.raises(ValueError):
        s = Switch()
        s.validate()


def test_import_export():
    from tests.output import BaseVoltage, BusbarSection, Voltage, UnitSymbol, UnitMultiplier, Decimal
    from tests.output import DocumentCIMRDF
    bv = BaseVoltage()
    v = Voltage()
    v.value, v.multiplier, v.unit = '69 k V'.split()
    bv.nominalVoltage = v
    document = DocumentCIMRDF([v, bv])
    document.dump()


def test_recover_from_xml():
    from tests.output import EquivalentInjection, Terminal, Switch, ConnectivityNode, DocumentCIMRDF

    ei = EquivalentInjection()
    ei.mRID = 'EquivalentNW243'
    t = Terminal()
    t.sequenceNumber = 1
    t.ConductingEquipment = ei

    s = Switch()
    s.normalOpen = True
    s.mRID = 'SW12'
    t1 = Terminal()
    t1.sequenceNumber = 1
    t1.ConductingEquipment = s
    t2 = Terminal()
    t2.sequenceNumber = 2
    t2.ConductingEquipment = s

    cn = ConnectivityNode()
    cn.mRID = 'Node23'
    cn.add_Terminals(t1)
    cn.add_Terminals(t)

    doc1 = DocumentCIMRDF([ei, t, s, t1, t2, cn])

    # Print to stdout
    doc1.dump()

    ###################################################
    # Convert to string
    string = doc1.tostring()

    ###################################################

    # Agente 2 (receptor)
    # Read the string to recover instances
    doc2 = DocumentCIMRDF()
    doc2.fromstring(string)
    instances = doc2.resources

    # Print to stdout again for comparison
    doc2.dump()

    a = list(instances)
    switches = list(filter(lambda x: isinstance(x, Switch), a))
    print(switches)

def test_new_version():

    from tests.output import EquivalentInjection, Terminal, Switch, ConnectivityNode, DocumentCIMRDF

    t1 = Terminal()
    t2 = Terminal()
    s1 = Switch(normalOpen=True, open=False, mRID='CH12', Terminals=[t1, t2])
    print(s1.Terminals)
    cn = ConnectivityNode(Terminals=[t1], mRID='COnnectivityNode')

    doc = DocumentCIMRDF([s1, t1, t2, cn])
    doc.dump()

def test_new_version_debug():
    from tests.output import Substation, Feeder, DocumentCIMRDF

    substation_1 = Substation(mRID='S1')
    substation_2 = Substation(mRID='S2')
    substation_3 = Substation(mRID='S3')

    feeder_1_s1 = Feeder(mRID='S1_AL1', FeedingSubstation=substation_1)
    feeder_2_s1 = Feeder(mRID='S1_AL2', FeedingSubstation=substation_1)
    feeder_3_s1 = Feeder(mRID='S1_AL3', FeedingSubstation=substation_1)
    feeder_4_s1 = Feeder(mRID='S1_AL4', FeedingSubstation=substation_1)

    feeder_1_s2 = Feeder(mRID='S2_AL1', FeedingSubstation=substation_2)
    feeder_2_s2 = Feeder(mRID='S2_AL2', FeedingSubstation=substation_2)

    feeder_1_s3 = Feeder(mRID='S3_AL1', FeedingSubstation=substation_3)

    doc = DocumentCIMRDF([substation_1, substation_2, substation_3, 
    feeder_1_s1, feeder_2_s1, feeder_3_s1, feeder_4_s1, feeder_1_s2, feeder_2_s2, feeder_1_s3])

    doc.dump()

    assert (substation_1.SubstationFeeder is substation_1.SubstationFeeder)
    assert not (substation_1.SubstationFeeder is substation_2.SubstationFeeder)

def test_recursive_add():
    from tests.output import Length, Decimal, BusbarSection, ACLineSegment, Terminal, Resistance, ConnectivityNode, UnitMultiplier, UnitSymbol, Reactance, DocumentCIMRDF

    d = DocumentCIMRDF()
    b = BusbarSection(
        mRID='sad', 
        Terminals=[
            Terminal(
                sequenceNumber=2, 
                ConnectivityNode=ConnectivityNode(
                    mRID='CN'
                )
            )
        ]
    )
    a = ACLineSegment(
            mRID='id', 
            r=Resistance('k', 'ohm', '123'), 
            x=Reactance('k', 'ohm', '123'), 
            x0=Reactance('k', 'ohm', '123'), 
            r0=Resistance('k', 'ohm', '123')
        )
    a.length = Length('none', 'm', '2342234.2342')
    d.add_recursively([b, a])

    d.dump()

    assert all(any(isinstance(obj, dtype) for obj in d.resources) for dtype in (Length, BusbarSection, Terminal, ConnectivityNode, Resistance, Reactance))
    assert all(all(not isinstance(obj, dtype) for dtype in (UnitMultiplier, UnitSymbol, Decimal)) for obj in d.resources)

def test_write_to_file():
    from tests.output import Length, Decimal, BusbarSection, ACLineSegment, Terminal, Resistance, ConnectivityNode, UnitMultiplier, UnitSymbol, Reactance, DocumentCIMRDF

    d = DocumentCIMRDF()
    b = BusbarSection(
        mRID='sad', 
        Terminals=[
            Terminal(
                sequenceNumber=2, 
                ConnectivityNode=ConnectivityNode(
                    mRID='CN'))])
    a = ACLineSegment(
        mRID='id', 
        r=Resistance('k', 'ohm', '123'), 
        x=Reactance('k', 'ohm', '123'), 
        x0=Reactance('k', 'ohm', '123'), 
        r0=Resistance('k', 'ohm', '123')
    )
    a.length = Length('none', 'm', '2342234.2342')
    d.add_recursively([b, a])

    d.dump()

    d.tofile('./tests/output.xml')


def test_read_from_file():
    from tests.output import Length, Decimal, BusbarSection, ACLineSegment, Terminal, Resistance, ConnectivityNode, UnitMultiplier, UnitSymbol, Reactance, DocumentCIMRDF

    d = DocumentCIMRDF()
    d.fromfile('./tests/output.xml')

    d.dump()

if __name__ == "__main__":
    test_output_generation()
    test_raises_validation_error()
    test_import_export()
    test_recover_from_xml()
    test_new_version()
    test_new_version_debug()
    test_recursive_add()
    test_write_to_file()
    test_read_from_file()