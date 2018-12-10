from unittest import TestCase
from dual_quaternions_ros import DualQuaternion
import numpy as np
import quaternion

import geometry_msgs.msg


class TestDualQuaternion(TestCase):

    def setUp(self):
        self.unit_dq = DualQuaternion.identity()
        self.random_dq = DualQuaternion.from_dq_array(np.array([1,2,3,4,5,6,7,8]))
        self.normalized_dq = self.random_dq.normalized

    def test_creation(self):
        # from dual quaternion array
        dq1 = DualQuaternion.from_dq_array(np.array([1, 2, 3, 4, 5, 6, 7, 8]))
        dq2 = DualQuaternion.from_dq_array([1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(dq1, dq2)
        # from quaternion + translation array
        dq3 = DualQuaternion.from_quat_pose_array(np.array([1, 2, 3, 4, 5, 6, 7]))
        dq4 = DualQuaternion.from_quat_pose_array([1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(dq3, dq4)
        # from ROS pose
        ros_pose = geometry_msgs.msg.Pose()
        ros_pose.orientation.w = 1.
        dq5 = DualQuaternion.from_ros_pose(ros_pose)
        self.assertEqual(dq5, self.unit_dq)
        self.assertEqual(dq5.ros_pose, ros_pose)
        # from ROS transform
        ros_transform = geometry_msgs.msg.Transform()
        ros_transform.rotation.w = 1.
        dq6 = DualQuaternion.from_ros_transform(ros_transform)
        self.assertEqual(dq5, dq6)
        self.assertEqual(dq6.ros_transform, ros_transform)
        # from homogeneous transformation matrix
        T = np.array([[1, 0, 0, 2], [0, 1, 0, 3], [0, 0, 1, 1], [0, 0, 0, 1]])
        dq7 = DualQuaternion.from_homogeneous_matrix(T)
        self.assertEqual(dq7.q_r, quaternion.one)
        self.assertEqual(dq7.translation, [2, 3, 1])
        self.assertEqual(dq7.homogeneous_matrix.all(), T.all())
        # from a point
        dq8 = DualQuaternion.from_translation_vector([4, 6, 8])
        self.assertEqual(dq8.translation, [4, 6, 8])

    def test_unit(self):
        q_r_unit = np.quaternion(1, 0, 0, 0)
        q_d_zero = np.quaternion(0, 0, 0, 0)
        unit_dq = DualQuaternion(q_r_unit, q_d_zero)
        self.assertEqual(self.unit_dq, unit_dq)
        # unit dual quaternion multiplied with another unit quaternion should yield unit
        self.assertEqual(self.unit_dq * self.unit_dq, self.unit_dq)

    def test_add(self):
        dq1 = DualQuaternion.from_translation_vector([4, 6, 8])
        dq2 = DualQuaternion.from_translation_vector([1, 2, 3])
        sum = dq1 + dq2
        self.assertEqual(sum.q_d, np.quaternion(0., 2.5, 4., 5.5))
        self.assertEqual(sum.translation, [5, 8, 11])

    def test_mult(self):
        # quaternion multiplication. Compare with homogeneous transformation matrices
        theta1 = np.pi / 180 * 20  # 20 deg
        T_pure_rot = np.array([[1., 0., 0., 0.],
                               [0., np.cos(theta1), -np.sin(theta1), 0.],
                               [0., np.sin(theta1), np.cos(theta1), 0.],
                               [0., 0., 0., 1.]])
        dq_pure_rot = DualQuaternion.from_homogeneous_matrix(T_pure_rot)
        T_pure_trans = np.array([[1., 0., 0., 1.],
                                 [0., 1., 0., 2.],
                                 [0., 0., 1., 3.],
                                 [0., 0., 0., 1.]])
        dq_pure_trans = DualQuaternion.from_homogeneous_matrix(T_pure_trans)

        T_double_rot = np.dot(T_pure_rot, T_pure_rot)
        dq_double_rot = dq_pure_rot * dq_pure_rot
        self.assertEqual(T_double_rot.all(), dq_double_rot.homogeneous_matrix.all())

        T_double_trans = np.dot(T_pure_trans, T_pure_trans)
        dq_double_trans = dq_pure_trans * dq_pure_trans
        self.assertEqual(T_double_trans.all(), dq_double_trans.homogeneous_matrix.all())

        # composed: trans and rot
        T_composed = np.dot(T_pure_rot, T_pure_trans)
        dq_composed = dq_pure_rot * dq_pure_trans
        self.assertEqual(T_composed.all(), dq_composed.homogeneous_matrix.all())


    def test_div(self):
        self.assertAlmostEqual(self.random_dq/self.random_dq, self.unit_dq)
        self.assertAlmostEqual(self.random_dq/self.unit_dq, self.random_dq)

    def test_inverse(self):
        self.assertAlmostEqual(self.unit_dq / self.random_dq, self.random_dq.inverse())

    def test_str_repr_is_string(self):
        # test that __str__ and __repr__ are working
        self.assertTrue(isinstance(repr(self.unit_dq), basestring))
        self.assertTrue(isinstance(self.unit_dq.__str__(), basestring))

    def test_conjugate(self):
        dq = self.normalized_dq * self.normalized_dq.conjugate()
        # a normalized quaternion multiplied with its conjugate should yield unit rotation
        self.assertAlmostEqual(dq.q_r, quaternion.one)

    def test_normalize(self):
        self.assertTrue(self.unit_dq.is_unit())
        self.assertEqual(self.unit_dq.normalized, self.unit_dq)
        unnormalized_dq = DualQuaternion.from_quat_pose_array([1, 2, 3, 4, 5, 6, 7])
        unnormalized_dq.normalize()  # now normalized!
        self.assertTrue(unnormalized_dq.is_unit())

    def test_transform(self):
        # transform a point from one frame (f2) to another (f1)
        point_f2 = [1, 1, 0]
        self.assertEqual(self.unit_dq.transform_point(point_f2), point_f2)

        # test that quaternion transform and matrix transform yield the same result
        T_f1_f2 = np.array([[1, 0, 0, 2], [0, 0.5403, -0.8415, 3], [0, 0.8415, 0.5403, 1], [0, 0, 0, 1]])
        dq_f1_f2 = DualQuaternion.from_homogeneous_matrix(T_f1_f2)

        # point is in f2, transformation will express it in f1
        point_f1_matrix = np.dot(T_f1_f2, np.expand_dims(np.array(point_f2 + [1]), 1))
        point_f1_dq = np.array(dq_f1_f2.transform_point(point_f2))
        self.assertEqual(point_f1_matrix[:3].T.all(), point_f1_dq.all())