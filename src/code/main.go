package main

func bubble_sort(arr [5]int32) [5]int32 {
    for i := 0; i < 5; i++ {
        for j := 0; j < 5-i; j++ {
            if (arr[j] < arr[j+1]) {
                temp := arr[j+1]
                arr[j+1] = arr[j]
                arr[j] = temp
            }
        }
    }
    return arr
}

func main() {
	var arr [5]int32
	arr[0] = 5
	arr[1] = 3
	arr[2] = 4
	arr[3] = 1
	arr[4] = 2
	sorted_arr := bubble_sort(arr)
	for i := 0; i < 5; i++ {
	    printf("%d -> %d\n", i, sorted_arr[i])
	}
}
