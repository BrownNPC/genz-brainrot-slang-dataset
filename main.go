package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// Terminal colors
const (
	Red     = "\033[0;31m"
	Green   = "\033[0;32m"
	Yellow  = "\033[0;33m"
	NoColor = "\033[0m"
)

// API configuration
const (
	APIBaseURL = "https://api.cloudflare.com/client/v4/accounts/YOUR-ACCOUNT-ID/ai/run/"
	APIKey     = "Bearer YOUR-API-KEY"
	Workers    = 6 // Number of concurrent workers
)

type Task struct {
	Index   int
	Prompt  string
	Example string
}

// Struct to hold processed data
type ProcessedDataItem struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

var (
	processedData []ProcessedDataItem
	dataLock      sync.Mutex
	wg            sync.WaitGroup
)

func saveData(filePath string) {
	dataLock.Lock()
	defer dataLock.Unlock()

	data, _ := json.MarshalIndent(processedData, "", "  ")
	if err := ioutil.WriteFile(filePath, data, 0644); err != nil {
		fmt.Printf("%sError saving data: %v%s\n", Red, err, NoColor)
	} else {
		fmt.Printf("%sData saved to '%s'.%s\n", Green, filePath, NoColor)
	}
}

func setupSignalHandler() {
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-signalChan
		fmt.Printf("\n%sInterrupt received. Saving data...%s\n", Red, NoColor)
		saveData("normal_data.json")
		os.Exit(0)
	}()
}

func runModel(model, prompt string) (map[string]interface{}, error) {
	data, _ := json.Marshal(map[string]interface{}{
		"messages": []map[string]string{
			{"role": "system", "content": prompt},
			{"role": "user", "content": prompt},
		},
	})

	req, err := http.NewRequest("POST", APIBaseURL+model, bytes.NewBuffer(data))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", APIKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var aiResp struct {
		Result struct {
			Response string `json:"response"`
		} `json:"result"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&aiResp); err != nil {
		return nil, err
	}

	var parsedResponse map[string]interface{}
	if err := json.Unmarshal([]byte(aiResp.Result.Response), &parsedResponse); err != nil {
		return nil, fmt.Errorf("failed to parse AI JSON response: %v", err)
	}
	return parsedResponse, nil
}
func worker(tasks <-chan Task, model string) {
	defer wg.Done()

	for task := range tasks {
		fmt.Printf("%sProcessing prompt %d: %s%s\n", Yellow, task.Index, task.Example, NoColor)
		for {
			response, err := runModel(model, task.Prompt)
			if err != nil {
				fmt.Printf("%sError processing prompt %d: %v%s\nRetrying...\n", Red, task.Index, err, NoColor)
				time.Sleep(1 * time.Second)
				continue
			}

			// Ensure the response is properly parsed
			parsedResponse, ok := response["response"].(string)
			if !ok || parsedResponse == "" {
				fmt.Printf("%sFailed to parse AI response for prompt %d. Retrying...\n", Red, task.Index, NoColor)
				time.Sleep(1 * time.Second)
				continue
			}

			fmt.Printf("%sProcessed prompt %d successfully.%s\n", Green, task.Index, NoColor)

			// Add to processed data
			dataLock.Lock()
			processedData = append(processedData,
				ProcessedDataItem{"user", task.Example},
				ProcessedDataItem{"assistant", parsedResponse},
			)
			dataLock.Unlock()

			break
		}
	}
}

func main() {
	setupSignalHandler()

	// Load prompts and examples
	promptsFile, _ := ioutil.ReadFile("genz_prompts.json")
	var prompts []string
	json.Unmarshal(promptsFile, &prompts)

	examplesFile, _ := ioutil.ReadFile("original_examples.json")
	var originalExamples []string
	json.Unmarshal(examplesFile, &originalExamples)

	tasks := make(chan Task, len(prompts))

	// Start workers
	for i := 0; i < Workers; i++ {
		wg.Add(1)
		go worker(tasks, "@cf/meta/llama-3-8b-instruct")
	}

	// Add tasks
	for i, prompt := range prompts {
		tasks <- Task{Index: i + 1, Prompt: prompt, Example: originalExamples[i]}
	}
	close(tasks)

	// Wait for all workers to finish
	wg.Wait()

	// Save final data
	saveData("normal_data.json")
	fmt.Println("Processing complete.")
}
