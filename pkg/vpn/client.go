package vpn

import (
	"bufio"
	"os"
	"os/exec"
	"runtime"
	"strings"

	// "github.com/davegallant/vpngate/pkg/exec"
	"github.com/juju/errors"
	"github.com/rs/zerolog/log"
)

// OpenVPNCmd 是全局的 OpenVPN 命令实例
var OpenVPNCmd *exec.Cmd

// Connect to a specified OpenVPN configuration
func Connect(configPath, statusFile string) error {
	tmpLogFile, err := os.CreateTemp("", "vpngate-openvpn-log-")
	if err != nil {
		return errors.Annotate(err, "Unable to create a temporary log file")
	}
	defer os.Remove(tmpLogFile.Name())

	// 清除旧的状态文件
	os.Remove(statusFile)

	executable := "openvpn"
	if runtime.GOOS == "windows" {
		executable = "C:\\Program Files\\OpenVPN\\bin\\openvpn.exe"
	}

	// err = exec.Run(
	// 	executable,
	// 	"./",
	// 	"--verb", "4",
	// 	"--config", configPath,
	// 	// "--data-ciphers-fallback",
	// 	// "AES-128-CBC",
	// 	"--data-ciphers", "AES-128-CBC",
	// 	"--remote-cert-tls", "server",
	// 	"--connect-retry-max", "2",
	// 	"--disable-dco",
	// 	"--session-timeout", "infinite",
	// 	"--ping-exit", "5",
	// 	"--ping-restart", "2",
	// 	"--connect-timeout", "1",
	// )
	// return err

	// 使用标准exec库
	OpenVPNCmd = exec.Command(
		executable,
		"--verb", "4",
		"--config", configPath,
		"--data-ciphers", "AES-128-CBC",
		"--remote-cert-tls", "server",
		"--connect-retry-max", "2",
		"--disable-dco",
		"--session-timeout", "infinite",
		"--ping-exit", "5",
		"--ping-restart", "2",
		"--connect-timeout", "2",
		"--status", statusFile, "2",
	)
	_, err1 := exec.LookPath(executable)
	if err1 != nil {
		log.Error().Msgf("%s is required, please install it", executable)
		os.Exit(1)
	}
	workDir := "."
	OpenVPNCmd.Dir = workDir
	log.Debug().Msgf("Executing " + strings.Join(OpenVPNCmd.Args, " "))

	stdout, err := OpenVPNCmd.StdoutPipe()
	if err != nil {
		log.Fatal().Err(err).Msg("无法获取 OpenVPN 进程的 stdout")
	}

	stderr, err := OpenVPNCmd.StderrPipe()
	if err != nil {
		log.Fatal().Err(err).Msg("无法获取 OpenVPN 进程的 stderr")
	}

	if err := OpenVPNCmd.Start(); err != nil {
		return errors.Annotate(err, "Failed to start OpenVPN")
	}

	go func() {
		scanner := bufio.NewScanner(stderr)
		for scanner.Scan() {
			log.Error().Msg(scanner.Text())
		}
	}()

	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		log.Debug().Msg(line)
		if strings.Contains(line, "Initialization Sequence Completed") {
			log.Debug().Msg("OpenVPN connection established")
			return nil
		}
	}
	if err := OpenVPNCmd.Wait(); err != nil {
		log.Debug().Msgf("Command finished with error: %v", err)
		return err
	}

	return err
}

// Disconnect stops the OpenVPN connection
func Disconnect() error {
	if OpenVPNCmd != nil && OpenVPNCmd.Process != nil {
		return OpenVPNCmd.Process.Kill()
	}
	return nil
}
