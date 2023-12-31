@0xd8bc192c6a4167ff; # unique file ID, generated by `capnp id`

using Cxx = import "/capnp/c++.capnp";
$Cxx.namespace("riaps::messages");

struct StabilizeVfMsg{
    sender @0: Text;
    timestamp @1: Float64;
    freqSetpointChange @2: Float64;
    reactivePower @3: Float64;
    activePower @4: Float64;
    voltageSetpointChange @5: Float64;
}
struct PrivateEstimatorMsg{
    sender @0: Int16;
    timestamp @1: Float64;
    reactivePower @2: Float64;
    powerEstimated @3: Float64;
    sStateEstimated @4: Float64;
    sw1 @5: Float64;
    sw2 @6: Float64;
    sw3 @7: Float64;
    sw4 @8: Float64;
    sw5 @9: Float64;
}

struct RelayMsg{
    sender @0: Text;
    timestamp @1: Float64;
    connected @2: Bool;
    freqSlip @3: Float64;
    voltDiff @4: Float64;
    angDiff @5: Float64;
    activePower @6: Float64;
    reactivePower @7: Float64;
    varms @8: Float64;
    frequency @9: Float64;
    msgcounter @10: Int64;
    synchronized @11: Bool;
    zeroPowerFlow @12: Bool;
}

# RelayMsgPQ does not seem to be used
struct RelayMsgPQ{
    sender @0: Text;
    timestamp @1: Float64;
    p @2: Float64;
    q @3: Float64;
}

struct SecConsensusMsg{
    sender @0: Text;
    timestamp @1: Float64;
    x @2: Float64;
    y @3: Float64;
}

struct OperatorMsg{
    sender @0: Text;
    type @1: Text;
    msgcounter @2: Int64;
    opalParams @3: List(Text);
    opalValues @4: List(Float64) = [0];
    requestedRelay @5: Text;
    requestedAction @6: Text;
    timestamp @7: Float64;
}

struct DgGeneralMsg{
    sender @0: Text;
    timestamp @1: Float64;
    activePower @2: Float64;
    reactivePower @3: Float64;
    incrementalCost @4: Float64;
    estimatedVoltageShare @5: List(Float64);
    msgcounter @6: Int64;
}

struct StateMsg{
    sender @0: Text;
    timestamp @1: Float64;
    msgcounter @2: Int64;
    currentState @3: Text;
    breaker @4: Text;
    action @5: Text;
    group @6: List(Text);
    reconfigcontrol@7: Bool;
}


struct GroupMsg{
    sender @0: Text;
    timestamp @1: Float64;
    msgcounter @2: Int64;
    group @3: List(Text);
    groupName @4: Text;
    requestedRelay @5: Text;
    requestedAction @6: Text;
    futureGroup @7: List(Text);
    futureGroupName @8: Text;
    commands @9: List(Float64) = [0];
}

