#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import boto3
from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import ClientError
from xc_common.logger import get_logger

# 获取模块专属logger
logger = get_logger("aws_s3")

max_pool_connections = 30


# 亚马逊
class AwsOSS(object):

    def __init__(self, aws_id=None, aws_key=None, aws_region_name=None, aws_endpoint=None, aws_bucket=None,
                 is_fast=False, fast_url=""):
        # 参数可以为空，允许延迟初始化
        self.aws_id = aws_id
        self.aws_key = aws_key
        self.aws_region_name = aws_region_name
        self.aws_endpoint = aws_endpoint
        self.bucket_name = aws_bucket
        self.is_fast = is_fast
        self.fast_url = fast_url
        self.client = None
        self.session = None

        # 如果提供了必要参数，则初始化S3客户端
        if all([aws_id, aws_key, aws_region_name, aws_endpoint, aws_bucket]):
            self._init_s3_client()

    def _init_s3_client(self):
        """初始化S3客户端"""
        try:
            config = Config(max_pool_connections=max_pool_connections)
            self.session = Session(
                aws_access_key_id=self.aws_id,
                aws_secret_access_key=self.aws_key,
                region_name=self.aws_region_name
            )
            self.client = self.session.client('s3', config=config, endpoint_url=f"https://{self.aws_endpoint}")
            logger.info(f"S3客户端初始化成功，区域: {self.aws_region_name}")
        except Exception as e:
            logger.error(f"S3客户端初始化失败: {str(e)}")

    @property
    def s3_client(self):
        return self.client

    def update_config(self, aws_id=None, aws_key=None, aws_region_name=None, aws_endpoint=None, aws_bucket=None,
                      is_fast=None, fast_url=None):
        """
        更新AWS配置并重新初始化客户端
        """
        # 更新配置
        if aws_id is not None: self.aws_id = aws_id
        if aws_key is not None: self.aws_key = aws_key
        if aws_region_name is not None: self.aws_region_name = aws_region_name
        if aws_endpoint is not None: self.aws_endpoint = aws_endpoint
        if aws_bucket is not None: self.bucket_name = aws_bucket
        if is_fast is not None: self.is_fast = is_fast
        if fast_url is not None: self.fast_url = fast_url

        # 重新初始化客户端
        self._init_s3_client()
        logger.info(f"AWS配置已更新，当前区域: {self.aws_region_name}")

    def get_s3_content(self, key_path):
        """
        从桶里获取对象的内容
        """
        # 检查客户端是否已初始化
        if not self.client:
            logger.error(f"获取S3对象失败: {key_path} - 客户端未初始化")
            return None

        try:
            logger.debug(f"尝试获取S3对象: {key_path}")
            bk_name = self.bucket_name
            response = self.s3_client.get_object(Bucket=bk_name, Key=key_path)
            stream = response.get('Body', None)
            if stream:
                content = str(stream.read(), encoding='utf-8')
                logger.debug(f"成功获取S3对象: {key_path}, 大小: {len(content)} 字节")
                return content
            logger.warning(f"S3对象 {key_path} 的Body为空")
            return None
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3客户端错误 ({error_code}) 获取对象 {key_path}: {str(e)}")
            if error_code == 'NoSuchKey':
                logger.error(f"S3对象不存在: {key_path}")
            elif error_code == 'AccessDenied':
                logger.error(f"没有权限访问S3对象: {key_path}")
            return None
        except Exception as e:
            logger.error(f"获取S3对象时发生未知错误 {key_path}: {str(e)}")
            return None
# 创建全局单例实例，供整个应用使用
aws_oss_singleton = AwsOSS()