#!/usr/bin/env python3
"""
NL2SQL自动化数据生成系统 - 主程序
支持两阶段LLM生成：规划 + 样本生成
"""

import os
import sys
import yaml
import argparse
import logging
from datetime import datetime

# 添加模块路径
sys.path.insert(0, os.path.dirname(__file__))

from modules.db_connector import create_connector
from modules.llm_client import create_llm_client
from modules.metadata_extractor import extract_and_save_metadata
from modules.table_cards import generate_and_save_table_cards
from modules.planner import generate_and_save_plan
from modules.generator import generate_and_save_samples
from modules.validator import validate_and_save_samples
from modules.exporter import export_samples


def setup_logging(log_dir: str = "./logs"):
    """
    配置日志系统
    
    Args:
        log_dir: 日志目录
    """
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"auto_nl2sql_{timestamp}.log")
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志文件: {log_file}")
    return logger


def load_config(config_path: str) -> dict:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def merge_config_with_args(config: dict, args: argparse.Namespace) -> dict:
    """
    合并配置文件和命令行参数
    
    Args:
        config: 配置字典
        args: 命令行参数
        
    Returns:
        合并后的配置字典
    """
    # 命令行参数优先级高于配置文件
    if args.db_host:
        config['db']['host'] = args.db_host
    if args.db_port:
        config['db']['port'] = args.db_port
    if args.db_user:
        config['db']['user'] = args.db_user
    if args.db_password:
        config['db']['password'] = args.db_password
    if args.db_database:
        config['db']['database'] = args.db_database
    
    if args.llm_api_base:
        config['llm']['api_base'] = args.llm_api_base
    if args.llm_api_key:
        config['llm']['api_key'] = args.llm_api_key
    if args.llm_model:
        config['llm']['model_name'] = args.llm_model
    
    if args.total_samples:
        config['generate']['total_samples'] = args.total_samples
    if args.output_path:
        config['generate']['output_path'] = args.output_path
    if args.output_format:
        config['generate']['output_format'] = args.output_format
    
    return config


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='NL2SQL自动化数据生成系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 配置文件
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='配置文件路径')
    
    # 数据库参数
    parser.add_argument('--db_host', type=str, help='数据库主机')
    parser.add_argument('--db_port', type=int, help='数据库端口')
    parser.add_argument('--db_user', type=str, help='数据库用户名')
    parser.add_argument('--db_password', type=str, help='数据库密码')
    parser.add_argument('--db_database', type=str, help='数据库名称')
    
    # LLM参数
    parser.add_argument('--llm_api_base', type=str, help='LLM API地址')
    parser.add_argument('--llm_api_key', type=str, help='LLM API密钥')
    parser.add_argument('--llm_model', type=str, help='LLM模型名称')
    
    # 生成参数
    parser.add_argument('--total_samples', type=int, help='生成样本总数')
    parser.add_argument('--output_path', type=str, help='输出文件路径')
    parser.add_argument('--output_format', type=str, choices=['alpaca', 'sharegpt'],
                       help='输出格式')
    
    # 其他参数
    parser.add_argument('--data_dir', type=str, default='./data',
                       help='数据输出目录')
    parser.add_argument('--skip_validation', action='store_true',
                       help='跳过SQL验证步骤')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    logger.info("=" * 80)
    logger.info("NL2SQL自动化数据生成系统启动")
    logger.info("=" * 80)
    
    try:
        # 1. 加载配置
        logger.info(f"加载配置文件: {args.config}")
        config = load_config(args.config)
        config = merge_config_with_args(config, args)
        
        # 创建数据目录
        os.makedirs(args.data_dir, exist_ok=True)
        
        # 2. 连接数据库
        logger.info("=" * 80)
        logger.info("阶段1: 数据库连接")
        logger.info("=" * 80)
        db_connector = create_connector(config['db'])
        db_connector.get_connection()
        
        # 3. 提取元数据
        logger.info("=" * 80)
        logger.info("阶段2: 提取数据库元数据")
        logger.info("=" * 80)
        metadata_path = os.path.join(args.data_dir, 'metadata.json')
        table_blacklist = config.get('security', {}).get('table_blacklist', [])
        metadata = extract_and_save_metadata(
            db_connector,
            metadata_path,
            table_blacklist
        )
        
        if not metadata:
            logger.error("未提取到任何表元数据，程序退出")
            return
        
        # 4. 生成表卡片
        logger.info("=" * 80)
        logger.info("阶段3: 生成表卡片")
        logger.info("=" * 80)
        table_cards_path = os.path.join(args.data_dir, 'table_cards.json')
        table_cards = generate_and_save_table_cards(metadata, table_cards_path)
        
        # 5. 创建LLM客户端
        logger.info("=" * 80)
        logger.info("阶段4: 初始化LLM客户端")
        logger.info("=" * 80)
        llm_client = create_llm_client(config['llm'])
        logger.info(f"LLM模型: {config['llm']['model_name']}")
        
        # 6. 生成主题规划（LLM阶段A）
        logger.info("=" * 80)
        logger.info("阶段5: 生成主题规划 (LLM阶段A)")
        logger.info("=" * 80)
        plan_path = os.path.join(args.data_dir, 'plan.json')
        plan = generate_and_save_plan(
            llm_client,
            table_cards,
            config['generate']['total_samples'],
            plan_path,
            config['generate'].get('min_tables_per_topic', 3),
            config['generate'].get('max_tables_per_topic', 8),
            config['generate'].get('dialect', 'mysql')
        )
        
        # 7. 生成样本（LLM阶段B）
        logger.info("=" * 80)
        logger.info("阶段6: 生成NL2SQL样本 (LLM阶段B)")
        logger.info("=" * 80)
        samples_raw_path = os.path.join(args.data_dir, 'samples_raw.jsonl')
        samples = generate_and_save_samples(
            llm_client,
            metadata,
            plan,
            samples_raw_path,
            config['generate'].get('dialect', 'mysql')
        )
        
        if not samples:
            logger.error("未生成任何样本，程序退出")
            return
        
        # 8. 验证SQL
        if not args.skip_validation:
            logger.info("=" * 80)
            logger.info("阶段7: SQL验证")
            logger.info("=" * 80)
            samples_valid_path = os.path.join(args.data_dir, 'samples_valid.jsonl')
            enable_execution = config['generate'].get('enable_execution_check', False)
            
            valid_samples = validate_and_save_samples(
                samples,
                metadata,
                samples_valid_path,
                config['generate'].get('dialect', 'mysql'),
                db_connector if enable_execution else None,
                enable_execution
            )
        else:
            logger.info("跳过SQL验证步骤")
            valid_samples = samples
        
        if not valid_samples:
            logger.error("没有有效样本，程序退出")
            return
        
        # 9. 导出训练数据
        logger.info("=" * 80)
        logger.info("阶段8: 导出训练数据")
        logger.info("=" * 80)
        output_path = config['generate']['output_path']
        output_format = config['generate'].get('output_format', 'alpaca')
        
        export_samples(
            valid_samples,
            output_path,
            output_format
        )
        
        # 10. 完成
        logger.info("=" * 80)
        logger.info("✅ 所有阶段完成！")
        logger.info("=" * 80)
        logger.info(f"总样本数: {len(samples)}")
        logger.info(f"有效样本数: {len(valid_samples)}")
        logger.info(f"输出文件: {output_path}")
        logger.info(f"输出格式: {output_format}")
        
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}", exc_info=True)
        sys.exit(1)
    
    finally:
        # 关闭数据库连接
        if 'db_connector' in locals():
            db_connector.close()


if __name__ == '__main__':
    main()

