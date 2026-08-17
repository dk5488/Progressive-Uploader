<?php
declare(strict_types=1);

class Config
{
	protected const string DB_NAME_DEFAULT = 'faved';
	protected const string STORAGE_PATH = ROOT_DIR . '/storage';

	protected const string IMAGE_STORAGE_DIR_NAME = 'img';

	public static function getDBPath(): string
	{
		$db_name = $_SERVER['DB_NAME'] ?? self::DB_NAME_DEFAULT;
		return sprintf('%s/%s.db', self::STORAGE_PATH, $db_name);
	}

	public static function getImageStoragePath(): string
	{
		return sprintf('%s/%s', self::STORAGE_PATH, self::IMAGE_STORAGE_DIR_NAME);
	}

	public static function getPasswordAlgo(): string
	{
		if (in_array(PASSWORD_ARGON2ID, password_algos())) {
			return PASSWORD_ARGON2ID;
		}
		return PASSWORD_DEFAULT;
	}

	public static function getSessionLifetime(): int
	{
		return 60 * 60 * 24 * 7; // 7 days
	}

	public static function getSessionCookieName(): string
	{
		return 'faved-session';
	}
}
