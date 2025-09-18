# encoding: utf-8
"""一键测试脚本"""
import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入项目模块
try:
    from utils import xray, is_root
    from core.utils import generate_random_string, generate_random_port
    from core.constants import DEFAULT_PORT_START, DEFAULT_PORT_END, RANDOM_STRING_LENGTH
    from utils.configFactory import Config
    from utils.color import *
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


class TestUtils(unittest.TestCase):
    """测试工具函数"""
    
    def test_generate_random_string(self):
        """测试生成随机字符串"""
        result = generate_random_string()
        self.assertEqual(len(result), RANDOM_STRING_LENGTH)
        self.assertTrue(result.isalnum())
        
        result_custom = generate_random_string(10)
        self.assertEqual(len(result_custom), 10)
    
    def test_generate_random_port(self):
        """测试生成随机端口"""
        port = generate_random_port()
        self.assertGreaterEqual(port, DEFAULT_PORT_START)
        self.assertLessEqual(port, DEFAULT_PORT_END)
    
    def test_gen_tag(self):
        """测试生成标签"""
        tags = Config.gen_tag("192.168.1.1")
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags[0], "in-192-168-1-1")
        self.assertEqual(tags[1], "out-192-168-1-1")
        self.assertEqual(tags[2], "192-168-1-1")
        
        tags2 = Config.gen_tag("127.0.0.1")
        self.assertEqual(tags2[0], "in-127-0-0-1")


class TestIPAddress(unittest.TestCase):
    """测试IP地址判断"""
    
    def test_is_private_ip(self):
        """测试内网IP判断"""
        self.assertTrue(xray.is_private_ip("192.168.1.1"))
        self.assertTrue(xray.is_private_ip("10.0.0.1"))
        self.assertTrue(xray.is_private_ip("172.16.0.1"))
        self.assertTrue(xray.is_private_ip("127.0.0.1"))
        self.assertFalse(xray.is_private_ip("8.8.8.8"))
        self.assertFalse(xray.is_private_ip("1.1.1.1"))


class TestConfig(unittest.TestCase):
    """测试配置类"""
    
    def setUp(self):
        """每个测试前创建临时配置文件"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.config_path_file = os.path.join(self.temp_dir, "test_config.json")
        self.config.log_path = self.temp_dir
    
    def test_init_config(self):
        """测试初始化配置"""
        self.config.init_config()
        self.assertIn("log", self.config.myconfig)
        self.assertIn("routing", self.config.myconfig)
        self.assertIn("rules", self.config.myconfig["routing"])
    
    def test_insert_block_config(self):
        """测试插入黑洞配置"""
        self.config.insert_block_config()
        outbounds = self.config.myconfig["outbounds"]
        self.assertEqual(len(outbounds), 1)
        self.assertEqual(outbounds[0]["protocol"], "blackhole")
        self.assertEqual(outbounds[0]["tag"], "out-block")
    
    def test_insert_black_domain(self):
        """测试添加黑名单域名"""
        self.config.init_config()
        self.config.insert_black_domain("example.com")
        
        rules = self.config.myconfig["routing"]["rules"]
        self.assertGreater(len(rules), 0)
        self.assertEqual(rules[0]["outboundTag"], "out-block")
        self.assertIn("example.com", rules[0]["domain"])
    
    def test_insert_multiple_black_domains(self):
        """测试添加多个黑名单域名"""
        self.config.init_config()
        self.config.insert_black_domain("example.com")
        self.config.insert_black_domain("test.com")
        
        rules = self.config.myconfig["routing"]["rules"]
        black_rule = rules[0]
        self.assertIn("example.com", black_rule["domain"])
        self.assertIn("test.com", black_rule["domain"])
    
    def test_write_and_read_config(self):
        """测试配置写入和读取"""
        self.config.init_config()
        self.config.insert_block_config()
        self.config.write_2_file()
        
        self.assertTrue(os.path.exists(self.config.config_path_file))
        
        with open(self.config.config_path_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        self.assertIn("log", loaded_config)
        self.assertIn("routing", loaded_config)
        self.assertIn("outbounds", loaded_config)
    
    def test_insert_routing_config(self):
        """测试插入路由配置"""
        self.config.init_config()
        self.config.insert_routing_config("in-tag", "out-tag")
        
        rules = self.config.myconfig["routing"]["rules"]
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["inboundTag"], ["in-tag"])
        self.assertEqual(rules[0]["outboundTag"], "out-tag")
    
    def test_insert_outbounds_config(self):
        """测试插入出站配置"""
        self.config.insert_outbounds_config("192.168.1.1", "out-tag")
        
        outbounds = self.config.myconfig["outbounds"]
        self.assertEqual(len(outbounds), 1)
        self.assertEqual(outbounds[0]["sendThrough"], "192.168.1.1")
        self.assertEqual(outbounds[0]["protocol"], "freedom")
        self.assertEqual(outbounds[0]["tag"], "out-tag")


class TestVMessConfig(unittest.TestCase):
    """测试VMess配置"""
    
    def setUp(self):
        """每个测试前创建临时配置文件"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.config_path_file = os.path.join(self.temp_dir, "test_config.json")
    
    def test_insert_vmess_raw(self):
        """测试插入VMess RAW配置"""
        uuid = "test-uuid-12345"
        tag = self.config.gen_tag("192.168.1.1")[0]
        
        self.config.insert_inbounds_vmess_config(
            ipaddr="192.168.1.1",
            port=10000,
            inbounds_tag=tag,
            uuids=uuid,
            alert_id=0,
            path="/",
            name="test-vmess",
            transport_layer="raw"
        )
        
        inbounds = self.config.myconfig["inbounds"]
        self.assertEqual(len(inbounds), 1)
        self.assertEqual(inbounds[0]["protocol"], "vmess")
        self.assertEqual(inbounds[0]["listen"], "192.168.1.1")
        self.assertEqual(inbounds[0]["port"], 10000)
        self.assertEqual(inbounds[0]["streamSettings"]["network"], "raw")
    
    def test_insert_vmess_ws(self):
        """测试插入VMess WebSocket配置"""
        uuid = "test-uuid-12345"
        tag = self.config.gen_tag("192.168.1.1")[0]
        
        self.config.insert_inbounds_vmess_config(
            ipaddr="192.168.1.1",
            port=10000,
            inbounds_tag=tag,
            uuids=uuid,
            alert_id=0,
            path="/path",
            name="test-vmess-ws",
            transport_layer="ws"
        )
        
        inbounds = self.config.myconfig["inbounds"]
        self.assertEqual(len(inbounds), 1)
        self.assertEqual(inbounds[0]["streamSettings"]["network"], "ws")
        self.assertIn("wsSettings", inbounds[0]["streamSettings"])


class TestSocks5Config(unittest.TestCase):
    """测试Socks5配置"""
    
    def setUp(self):
        """每个测试前创建临时配置文件"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.config_path_file = os.path.join(self.temp_dir, "test_config.json")
    
    def test_insert_socks5_config(self):
        """测试插入Socks5配置"""
        tag = self.config.gen_tag("192.168.1.1")[0]
        
        self.config.insert_inbounds_sk5_config(
            ipaddr="192.168.1.1",
            port=10000,
            inbounds_tag=tag,
            user="testuser",
            passwd="testpass",
            name="test-socks5",
            network_layer_support_udp=False
        )
        
        inbounds = self.config.myconfig["inbounds"]
        self.assertEqual(len(inbounds), 1)
        self.assertEqual(inbounds[0]["protocol"], "socks")
        self.assertEqual(inbounds[0]["settings"]["auth"], "password")
        self.assertEqual(inbounds[0]["settings"]["udp"], False)
        self.assertEqual(inbounds[0]["settings"]["accounts"][0]["user"], "testuser")
        self.assertEqual(inbounds[0]["settings"]["accounts"][0]["pass"], "testpass")
    
    def test_insert_socks5_udp(self):
        """测试插入支持UDP的Socks5配置"""
        tag = self.config.gen_tag("192.168.1.1")[0]
        
        self.config.insert_inbounds_sk5_config(
            ipaddr="192.168.1.1",
            port=10000,
            inbounds_tag=tag,
            user="testuser",
            passwd="testpass",
            name="test-socks5-udp",
            network_layer_support_udp=True
        )
        
        inbounds = self.config.myconfig["inbounds"]
        self.assertEqual(inbounds[0]["settings"]["udp"], True)


class TestModuleImport(unittest.TestCase):
    """测试模块导入"""
    
    def test_import_main_modules(self):
        """测试导入主模块"""
        try:
            from utils import xray, publish
            from core import constants, utils
            from models import config_templates
            from models.config_templates import (
                create_inbound_config, create_log_config, 
                create_routing_config, create_stream_settings
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"模块导入失败: {e}")
    
    def test_xray_instance(self):
        """测试Xray实例"""
        self.assertIsNotNone(xray)
        self.assertIsInstance(xray, Config)


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行测试...")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestUtils,
        TestIPAddress,
        TestConfig,
        TestVMessConfig,
        TestSocks5Config,
        TestModuleImport
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print("=" * 60)
    
    # 如果有失败或错误，返回非零退出码
    if result.failures or result.errors:
        return 1
    return 0


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
