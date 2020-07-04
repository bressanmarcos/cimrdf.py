import builtins
import io
import os
import sys
import pytest
from unittest.mock import patch
sys.path.insert(0, '../')
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
    with patch.object(sys, 'argv', ['', 'test_rdfs.xml', 'output.py']):
        generator.main()


def test_raises_validation_error():
    from output import Switch
    with pytest.raises(ValueError):
        s = Switch()
        s.validate()


def test_import_export():
    from output import BaseVoltage, BusbarSection, Voltage, UnitSymbol, UnitMultiplier, Decimal
    from output import DocumentCIMRDF
    from xml.etree import ElementTree as ET
    bv = BaseVoltage()
    v = Voltage()
    v.Voltage_multiplier = UnitMultiplier(UnitMultiplier.K)
    v.Voltage_unit = UnitSymbol(UnitSymbol.NONE)
    v.Voltage_value = '2.001'
    bv.BaseVoltage_nominalVoltage = v
    document = DocumentCIMRDF([v, bv])
    document.dump()


def test_recover_from_xml():
    from output import EquivalentInjection, Terminal, Switch, ConnectivityNode, DocumentCIMRDF

    ei = EquivalentInjection()
    ei.IdentifiedObject_mRID = 'EquivalentNW243'
    t = Terminal()
    t.Terminal_sequenceNumber = 1
    t.Terminal_ConductingEquipment = ei

    s = Switch()
    s.Switch_normalOpen = True
    s.IdentifiedObject_mRID = 'SW12'
    t1 = Terminal()
    t1.Terminal_sequenceNumber = 1
    t1.Terminal_ConductingEquipment = s
    t2 = Terminal()
    t2.Terminal_sequenceNumber = 2
    t2.Terminal_ConductingEquipment = s

    cn = ConnectivityNode()
    cn.IdentifiedObject_mRID = 'Node23'
    cn.ConnectivityNode_Terminals = [t1, t]

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

    from output import EquivalentInjection, Terminal, Switch, ConnectivityNode, DocumentCIMRDF

    t1 = Terminal()
    t2 = Terminal()
    s1 = Switch(Switch_normalOpen=True, Switch_open=False, IdentifiedObject_mRID='CH12', ConductingEquipment_Terminals=[t1, t2])
    print(s1.ConductingEquipment_Terminals)
    cn = ConnectivityNode(ConnectivityNode_Terminals=[t1], IdentifiedObject_mRID='COnnectivityNode')

    doc = DocumentCIMRDF([s1, t1, t2, cn])
    doc.dump()

def test_new_version_debug():
    from output import Substation, Feeder, DocumentCIMRDF

    substation_1 = Substation(IdentifiedObject_mRID='S1')
    substation_2 = Substation(IdentifiedObject_mRID='S2')
    substation_3 = Substation(IdentifiedObject_mRID='S3')

    feeder_1_s1 = Feeder(IdentifiedObject_mRID='S1_AL1', Feeder_FeedingSubstation=substation_1)
    feeder_2_s1 = Feeder(IdentifiedObject_mRID='S1_AL2', Feeder_FeedingSubstation=substation_1)
    feeder_3_s1 = Feeder(IdentifiedObject_mRID='S1_AL3', Feeder_FeedingSubstation=substation_1)
    feeder_4_s1 = Feeder(IdentifiedObject_mRID='S1_AL4', Feeder_FeedingSubstation=substation_1)

    feeder_1_s2 = Feeder(IdentifiedObject_mRID='S2_AL1', Feeder_FeedingSubstation=substation_2)
    feeder_2_s2 = Feeder(IdentifiedObject_mRID='S2_AL2', Feeder_FeedingSubstation=substation_2)

    feeder_1_s3 = Feeder(IdentifiedObject_mRID='S3_AL1', Feeder_FeedingSubstation=substation_3)

    doc = DocumentCIMRDF([substation_1, substation_2, substation_3, 
    feeder_1_s1, feeder_2_s1, feeder_3_s1, feeder_4_s1, feeder_1_s2, feeder_2_s2, feeder_1_s3])

    doc.dump()

    assert (substation_1.Substation_SubstationFeeder is substation_1.Substation_SubstationFeeder)
    assert not (substation_1.Substation_SubstationFeeder is substation_2.Substation_SubstationFeeder)

def test_recursive_add():
    from output import Length, Decimal, BusbarSection, ACLineSegment, Terminal, Resistance, ConnectivityNode, UnitMultiplier, UnitSymbol, Reactance, DocumentCIMRDF

    d = DocumentCIMRDF()
    b = BusbarSection(
        IdentifiedObject_mRID='sad', 
        ConductingEquipment_Terminals=[
            Terminal(
                Terminal_sequenceNumber=2, 
                Terminal_ConnectivityNode=ConnectivityNode(
                    IdentifiedObject_mRID='CN'))])
    a = ACLineSegment(IdentifiedObject_mRID='id', ACLineSegment_r=Resistance(UnitMultiplier('k'), UnitSymbol('ohm'), Decimal('123')), ACLineSegment_x=Reactance(UnitMultiplier('k'), UnitSymbol('ohm'), Decimal('123')), ACLineSegment_x0=Reactance(UnitMultiplier('k'), UnitSymbol('ohm'), Decimal('123')), ACLineSegment_r0=Resistance(UnitMultiplier('k'), UnitSymbol('ohm'), Decimal('123')))
    a.Conductor_length = Length(UnitMultiplier('none'), UnitSymbol('m'), Decimal('2342234.2342'))
    d.add_recursively([b, a])

    d.dump()

# test_recursive_add()