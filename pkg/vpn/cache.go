package vpn

import (
	"encoding/json"
	"io"
	"os"
	"path"
	"time"

	"github.com/rs/zerolog/log"
	"github.com/spf13/afero"
)

const serverCachefile = "servers.json"

func getCacheDir() string {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		log.Error().Msgf("Failed to get user's home directory: %s ", err)
		return ""
	}
	cacheDir := path.Join(homeDir, ".vpngate", "cache")
	return cacheDir
}

func createCacheDir() error {
	cacheDir := getCacheDir()
	AppFs := afero.NewOsFs()
	return AppFs.MkdirAll(cacheDir, 0o700)
}

func getVpnListCache() (*[]Server, error) {
	cacheFile := path.Join(getCacheDir(), serverCachefile)
	
	serversFile, err := os.Open(cacheFile)
	if err != nil {
		return nil, err
	}

	byteValue, err := io.ReadAll(serversFile)
	if err != nil {
		return nil, err
	}

	var servers []Server

	err = json.Unmarshal(byteValue, &servers)

	if err != nil {
		return nil, err
	}

	return &servers, nil
}

func writeVpnListToCache(servers []Server) error {
	err := createCacheDir()
	if err != nil {
		return err
	}

	f, err := json.MarshalIndent(servers, "", " ")
	if err != nil {
		return err
	}

	cacheFile := path.Join(getCacheDir(), serverCachefile)

	err = os.WriteFile(cacheFile, f, 0o644)

	return err
}

func vpnListCacheIsExpired() bool {
	file, err := os.Stat(path.Join(getCacheDir(), serverCachefile))
	if err != nil {
		return true
	}

	lastModified := file.ModTime()

	return (time.Since(lastModified)) > time.Duration(8*time.Hour)
}
