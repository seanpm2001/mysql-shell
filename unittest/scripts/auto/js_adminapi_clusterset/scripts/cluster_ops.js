//@ {VER(>=8.0.27)}

// Tests various positive and negative scenarios for InnoDB Cluster operations
// on Clusters that are part of a ClusterSet.

//@<> INCLUDE clusterset_utils.inc

//@<> Setup + Create primary cluster + add Replica Cluster
var scene = new ClusterScenario([__mysql_sandbox_port1, __mysql_sandbox_port2]);
var session = scene.session
var cluster = scene.cluster
testutil.deploySandbox(__mysql_sandbox_port3, "root", {report_host: hostname});
testutil.deploySandbox(__mysql_sandbox_port4, "root", {report_host: hostname});
testutil.deploySandbox(__mysql_sandbox_port5, "root", {report_host: hostname});

cs = cluster.createClusterSet("domain");

replicacluster = cs.createReplicaCluster(__sandbox_uri3, "replica");
replicacluster.addInstance(__sandbox_uri4);

CHECK_REPLICA_CLUSTER([__sandbox_uri3, __sandbox_uri4], cluster, replicacluster);
EXPECT_OUTPUT_CONTAINS("* Configuring ClusterSet managed replication channel...");
EXPECT_OUTPUT_CONTAINS("** Changing replication source of <<<hostname>>>:<<<__mysql_sandbox_port4>>> to <<<hostname>>>:<<<__mysql_sandbox_port1>>>");

// Cluster topology changes that affect the replication channel between cluster update the replication channels accordingly:
//   - When the primary instance is removed (of either REPLICA or PRIMARY cluster).
//   - When the primary instance is changed (of either REPLICA or PRIMARY cluster).
//   - When the quorum is forced (of REPLICA cluster).
//   - When the cluster is rebooted from complete outage.

//@<> Removing the primary instance of the REPLICA Cluster must ensure the replication stream is kept and reset all CS settings
replicacluster.removeInstance(__sandbox_uri3);

shell.connect(__sandbox_uri4);
replicacluster = dba.getCluster();

CHECK_REPLICA_CLUSTER([__sandbox_uri4], cluster, replicacluster);
CHECK_PRIMARY_CLUSTER([__sandbox_uri1, __sandbox_uri2], cluster);
CHECK_REMOVED_INSTANCE(__sandbox_uri3);

//@<> Removing the primary instance of the PRIMARY Cluster must ensure the replication stream is kept and reset all CS settings
cluster.removeInstance(__sandbox_uri1);
CHECK_REMOVED_INSTANCE(__sandbox_uri1);

shell.connect(__sandbox_uri2);
cluster = dba.getCluster();

shell.connect(__sandbox_uri4);
replicacluster = dba.getCluster();

ensure_cs_replication_channel_ready(__sandbox_uri2, __mysql_sandbox_port2);

CHECK_PRIMARY_CLUSTER([__sandbox_uri2], cluster);
CHECK_REPLICA_CLUSTER([__sandbox_uri4], cluster, replicacluster);

// Add back the instances to the clusters
cluster.addInstance(__sandbox_uri1);

// Test setting super_read_only to false in the removed member and add it back to verify it's enabled back
var session3 = mysql.getSession(__sandbox_uri3);
session3.runSql("SET GLOBAL super_read_only=0");

replicacluster.addInstance(__sandbox_uri3);

CHECK_REPLICA_CLUSTER([__sandbox_uri4, __sandbox_uri3], cluster, replicacluster);

//@<> Changing the primary instance of the PRIMARY Cluster must ensure the replication stream is kept
cluster.setPrimaryInstance(__sandbox_uri1);

shell.connect(__sandbox_uri1);
cluster = dba.getCluster();

shell.connect(__sandbox_uri4);
replicacluster = dba.getCluster();

ensure_cs_replication_channel_ready(__sandbox_uri4, __mysql_sandbox_port1);

CHECK_PRIMARY_CLUSTER([__sandbox_uri1, __sandbox_uri2], cluster);
CHECK_REPLICA_CLUSTER([__sandbox_uri4, __sandbox_uri3], cluster, replicacluster);

//@<> Changing the primary instance of the REPLICA Cluster must ensure the replication stream is kept
replicacluster.setPrimaryInstance(__sandbox_uri3);

CHECK_PRIMARY_CLUSTER([__sandbox_uri1, __sandbox_uri2], cluster);
CHECK_REPLICA_CLUSTER([__sandbox_uri3, __sandbox_uri4], cluster, replicacluster);

//@<> rejoinInstance on a replica cluster
shell.connect(__sandbox_uri3);
replicacluster = dba.getCluster();

var session4 = mysql.getSession(__sandbox_uri4);
session4.runSql("STOP group_replication");

// Disable skip_replica_start to verify that rejoin enables it back
session4.runSql("SET PERSIST_ONLY skip_replica_start=0");
// Disable start_on_boot
session4.runSql("SET PERSIST_ONLY group_replication_start_on_boot=0");
testutil.restartSandbox(__mysql_sandbox_port4);

EXPECT_NO_THROWS(function() { replicacluster.rejoinInstance(__sandbox_uri4); });
EXPECT_OUTPUT_CONTAINS("* Waiting for the Cluster to synchronize with the PRIMARY Cluster...");
EXPECT_OUTPUT_CONTAINS("* Configuring ClusterSet managed replication channel...");
EXPECT_OUTPUT_CONTAINS("** Changing replication source of <<<hostname>>>:<<<__mysql_sandbox_port4>>> to <<<hostname>>>:<<<__mysql_sandbox_port1>>>");

testutil.waitMemberState(__mysql_sandbox_port4, "ONLINE");

CHECK_REPLICA_CLUSTER([__sandbox_uri3, __sandbox_uri4], cluster, replicacluster);
CHECK_REJOINED_INSTANCE(__sandbox_uri4, cluster, false);

// GTID sync operations must use the primary instance of the PRIMARY cluster as the source, the sync happens in:
//   - cluster.removeInstance()

//@<> Verify that a transaction sync happens before the removal of the instance in a REPLICA cluster
shell.connect(__sandbox_uri1);
var session4 = mysql.getSession(__sandbox_uri4);

// Remove instance from REPLICA Cluster
replicacluster.removeInstance(__sandbox_uri4);
CHECK_GTID_CONSISTENT(session, session4);
CHECK_REPLICA_CLUSTER([__sandbox_uri3], cluster, replicacluster);
CHECK_REMOVED_INSTANCE(__sandbox_uri4);

// Add back the instance to the cluster
replicacluster.addInstance(__sandbox_uri4, {recoveryMethod: "clone"});
var session4 = mysql.getSession(__sandbox_uri4);

//@<> Remove instance and add it back as a new replica cluster via incremental {false}
replicacluster.removeInstance(__sandbox_uri4);

nc = cs.createReplicaCluster(__sandbox_uri4, "newcluster", {recoveryMethod:"incremental"});

//@<> Put it back {false}
cs.removeCluster("newcluster");

// session4.runSql("stop group_replication");

replicacluster.addInstance(__sandbox_uri4);


//@<> Remove instance from cluster and add to another one
// the instance will have view change GTIDs from the old cluster that don't exist in the primary
replicacluster.removeInstance(__sandbox_uri4);

c3 = cs.createReplicaCluster(__sandbox_uri5, "cluster3", {recoveryMethod:"incremental", communicationStack: "MYSQL"});
c3.addInstance(__sandbox_uri4);

c3.removeInstance(__sandbox_uri4);

// <Cluster>.rejoinInstance() must verify the value of skip_slave_start and enabled it if necessary and if the cluster belongs to a ClusterSet

//@<> rejoinInstance on a primary cluster
var session2 = mysql.getSession(__sandbox_uri2);
session2.runSql("STOP group_replication");

// Disable skip_replica_start to verify that rejoin enables it back
session2.runSql("SET PERSIST_ONLY skip_replica_start=0");
// Disable start_on_boot
session2.runSql("SET PERSIST_ONLY group_replication_start_on_boot=0");
testutil.restartSandbox(__mysql_sandbox_port2);

EXPECT_NO_THROWS(function() { cluster.rejoinInstance(__sandbox_uri2); });

testutil.waitMemberState(__mysql_sandbox_port2, "ONLINE");

CHECK_PRIMARY_CLUSTER([__sandbox_uri1, __sandbox_uri2], cluster);
CHECK_REJOINED_INSTANCE(__sandbox_uri2);

//@<> rejoinInstance on a replica cluster when primary cluster is under heavy load

// Rejoining an instance to a Replica Cluster when 'MySQL' comm stack is used
// (default) and the Primary Cluster is under heavy load results in a failure:
// the instance is unable to rejoin the Cluster.
// The problem is that a new recovery account is created on the primary Cluster
// so then is replicated everywhere else but since the primary is under a heavy
// load, the account wasn't replicated yet to the replica cluster and
// rejoining a member of the replica cluster fails since GR does
// pre-authentication using the recovery accounts before actually joining the
// group, when using the MySQL comm stack. With the XCom communication stack
// the instance will rejoin the group and be stuck in RECOVERING state for a while.

// Add instance 4 to the replica cluster
c3.addInstance(__sandbox_uri4);

var session4 = mysql.getSession(__sandbox_uri4);
session4.runSql("STOP group_replication");
session4.runSql("SET PERSIST_ONLY group_replication_start_on_boot=0");
testutil.restartSandbox(__mysql_sandbox_port4);

// simulate lag by introducing delay in the replication channel with
// SOURCE_DELAY. The value must be >50 seconds to ensure the join fails since GR
// attempts 10 times the join with an interval of 5 seconds between attempt
var session5 = mysql.getSession(__sandbox_uri5);
session5.runSql("STOP REPLICA FOR CHANNEL 'clusterset_replication'");
session5.runSql("CHANGE REPLICATION SOURCE TO SOURCE_DELAY=60 FOR CHANNEL 'clusterset_replication'");
session5.runSql("START REPLICA FOR CHANNEL 'clusterset_replication'");

// Attempt to rejoin the instance
EXPECT_NO_THROWS(function() { c3.rejoinInstance(__sandbox_uri4); });
EXPECT_OUTPUT_CONTAINS("* Waiting for the Cluster to synchronize with the PRIMARY Cluster...");
EXPECT_OUTPUT_CONTAINS("* Configuring ClusterSet managed replication channel...");
EXPECT_OUTPUT_CONTAINS("** Changing replication source of <<<hostname>>>:<<<__mysql_sandbox_port4>>> to <<<hostname>>>:<<<__mysql_sandbox_port1>>>");

shell.connect(__sandbox_uri5);
testutil.waitMemberState(__mysql_sandbox_port4, "ONLINE");

CHECK_REPLICA_CLUSTER([__sandbox_uri5, __sandbox_uri4], cluster, c3);
CHECK_REJOINED_INSTANCE(__sandbox_uri4, c3, false);

//@<> createCluster() must generate and set a value for group_replication_view_change_uuid
var session4 = mysql.getSession(__sandbox_uri4);
reset_instance(session4);
testutil.stopSandbox(__mysql_sandbox_port3);
shell.connect(__sandbox_uri4);
dba.createCluster("newcluster");

var view_change_uuid = session.runSql("select @@global.group_replication_view_change_uuid").fetchOne()[0];
EXPECT_NE(null, view_change_uuid);

var view_change_uuid_md = session.runSql("select (attributes->>'$.group_replication_view_change_uuid') from mysql_innodb_cluster_metadata.clusters where cluster_name='newcluster'").fetchOne()[0];
EXPECT_EQ(view_change_uuid_md, view_change_uuid);

//@<> Cleanup
scene.destroy();
testutil.destroySandbox(__mysql_sandbox_port3);
testutil.destroySandbox(__mysql_sandbox_port4);
testutil.destroySandbox(__mysql_sandbox_port5);
