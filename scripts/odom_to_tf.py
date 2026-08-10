#!/usr/bin/env python3

from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from tf2_ros import TransformBroadcaster


class OdomToTf(Node):
    """Publish the transform contained in the robot's odometry messages."""

    def __init__(self):
        super().__init__('odom_to_tf')
        self.declare_parameter('odom_topic', '/odom')
        odom_topic = self.get_parameter('odom_topic').value

        self._broadcaster = TransformBroadcaster(self)
        self._subscription = self.create_subscription(
            Odometry,
            odom_topic,
            self._odom_callback,
            qos_profile_sensor_data,
        )
        self.get_logger().info(
            f'Publishing odometry messages from {odom_topic} as TF.'
        )

    def _odom_callback(self, msg):
        if not msg.header.frame_id or not msg.child_frame_id:
            self.get_logger().warn(
                'Odometry message has an empty frame_id or child_frame_id.',
                throttle_duration_sec=5.0,
            )
            return

        transform = TransformStamped()
        transform.header.stamp = msg.header.stamp
        transform.header.frame_id = msg.header.frame_id
        transform.child_frame_id = msg.child_frame_id
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = msg.pose.pose.position.z
        transform.transform.rotation = msg.pose.pose.orientation
        self._broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTf()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
