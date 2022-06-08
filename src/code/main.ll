; ModuleID = "main"
target triple = "x86_64-apple-darwin19.6.0"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

define <5 x i32> @"bubble_sort"(<5 x i32> %"arr")
{
entry:
  %"arr.1" = alloca <5 x i32>
  store <5 x i32> %"arr", <5 x i32>* %"arr.1"
  %"i" = alloca i32
  store i32 0, i32* %"i"
  %"i.1" = load i32, i32* %"i"
  %".5" = icmp slt i32 %"i.1", 5
  br i1 %".5", label %"entry.if", label %"entry.endif"
for_loop:
  %"j" = alloca i32
  store i32 0, i32* %"j"
  %"i.2" = load i32, i32* %"i"
  %".9" = sub i32 5, %"i.2"
  %"j.1" = load i32, i32* %"j"
  %".10" = icmp slt i32 %"j.1", %".9"
  br i1 %".10", label %"for_loop.if", label %"for_loop.endif"
entry.if:
  br label %"for_loop"
entry.endif:
  %"arr.1.9" = load <5 x i32>, <5 x i32>* %"arr.1"
  ret <5 x i32> %"arr.1.9"
for_loop.1:
  %"j.2" = load i32, i32* %"j"
  %".13" = add i32 %"j.2", 1
  %"arr.1.1" = load <5 x i32>, <5 x i32>* %"arr.1"
  %"arr.1.1.1" = extractelement <5 x i32> %"arr.1.1", i32 %".13"
  %"arr.1.2" = load <5 x i32>, <5 x i32>* %"arr.1"
  %"j.3" = load i32, i32* %"j"
  %"arr.1.2.1" = extractelement <5 x i32> %"arr.1.2", i32 %"j.3"
  %".14" = icmp slt i32 %"arr.1.2.1", %"arr.1.1.1"
  br i1 %".14", label %"for_loop.1.if", label %"for_loop.1.endif"
for_loop.if:
  br label %"for_loop.1"
for_loop.endif:
  %"i.4" = load i32, i32* %"i"
  %".29" = add i32 %"i.4", 1
  store i32 %".29", i32* %"i"
  %"i.5" = load i32, i32* %"i"
  %".31" = icmp slt i32 %"i.5", 5
  br i1 %".31", label %"for_loop.endif.if", label %"for_loop.endif.endif"
for_loop.1.if:
  %"j.4" = load i32, i32* %"j"
  %".16" = add i32 %"j.4", 1
  %"arr.1.3" = load <5 x i32>, <5 x i32>* %"arr.1"
  %"arr.1.3.1" = extractelement <5 x i32> %"arr.1.3", i32 %".16"
  %"temp" = alloca i32
  store i32 %"arr.1.3.1", i32* %"temp"
  %"j.5" = load i32, i32* %"j"
  %".18" = add i32 %"j.5", 1
  %"arr.1.4" = load <5 x i32>, <5 x i32>* %"arr.1"
  %"j.6" = load i32, i32* %"j"
  %"arr.1.4.1" = extractelement <5 x i32> %"arr.1.4", i32 %"j.6"
  %"arr.1.5" = load <5 x i32>, <5 x i32>* %"arr.1"
  %"arr.1.6" = insertelement <5 x i32> %"arr.1.5", i32 %"arr.1.4.1", i32 %".18"
  store <5 x i32> %"arr.1.6", <5 x i32>* %"arr.1"
  %"j.7" = load i32, i32* %"j"
  %"temp.1" = load i32, i32* %"temp"
  %"arr.1.7" = load <5 x i32>, <5 x i32>* %"arr.1"
  %"arr.1.8" = insertelement <5 x i32> %"arr.1.7", i32 %"temp.1", i32 %"j.7"
  store <5 x i32> %"arr.1.8", <5 x i32>* %"arr.1"
  br label %"for_loop.1.endif"
for_loop.1.endif:
  %"j.8" = load i32, i32* %"j"
  %".22" = add i32 %"j.8", 1
  store i32 %".22", i32* %"j"
  %"i.3" = load i32, i32* %"i"
  %".24" = sub i32 5, %"i.3"
  %"j.9" = load i32, i32* %"j"
  %".25" = icmp slt i32 %"j.9", %".24"
  br i1 %".25", label %"for_loop.1.endif.if", label %"for_loop.1.endif.endif"
for_loop.1.endif.if:
  br label %"for_loop.1"
for_loop.1.endif.endif:
  br label %"for_loop.endif"
for_loop.endif.if:
  br label %"for_loop"
for_loop.endif.endif:
  br label %"entry.endif"
}

define void @"main"()
{
entry:
  %"arr" = alloca <5 x i32>
  %"arr.1" = load <5 x i32>, <5 x i32>* %"arr"
  %"arr.2" = insertelement <5 x i32> %"arr.1", i32 5, i32 0
  store <5 x i32> %"arr.2", <5 x i32>* %"arr"
  %"arr.3" = load <5 x i32>, <5 x i32>* %"arr"
  %"arr.4" = insertelement <5 x i32> %"arr.3", i32 3, i32 1
  store <5 x i32> %"arr.4", <5 x i32>* %"arr"
  %"arr.5" = load <5 x i32>, <5 x i32>* %"arr"
  %"arr.6" = insertelement <5 x i32> %"arr.5", i32 4, i32 2
  store <5 x i32> %"arr.6", <5 x i32>* %"arr"
  %"arr.7" = load <5 x i32>, <5 x i32>* %"arr"
  %"arr.8" = insertelement <5 x i32> %"arr.7", i32 1, i32 3
  store <5 x i32> %"arr.8", <5 x i32>* %"arr"
  %"arr.9" = load <5 x i32>, <5 x i32>* %"arr"
  %"arr.10" = insertelement <5 x i32> %"arr.9", i32 2, i32 4
  store <5 x i32> %"arr.10", <5 x i32>* %"arr"
  %"arr.11" = load <5 x i32>, <5 x i32>* %"arr"
  %".7" = call <5 x i32> @"bubble_sort"(<5 x i32> %"arr.11")
  %"sorted_arr" = alloca <5 x i32>
  store <5 x i32> %".7", <5 x i32>* %"sorted_arr"
  %"i" = alloca i32
  store i32 0, i32* %"i"
  %"i.1" = load i32, i32* %"i"
  %".10" = icmp slt i32 %"i.1", 5
  br i1 %".10", label %"entry.if", label %"entry.endif"
for_loop:
  %"i.2" = load i32, i32* %"i"
  %"sorted_arr.1" = load <5 x i32>, <5 x i32>* %"sorted_arr"
  %"i.3" = load i32, i32* %"i"
  %"sorted_arr.1.1" = extractelement <5 x i32> %"sorted_arr.1", i32 %"i.3"
  %".13" = bitcast [9 x i8]* @"function_main_VoidType_31791" to i8*
  %".14" = call i32 (i8*, ...) @"printf"(i8* %".13", i32 %"i.2", i32 %"sorted_arr.1.1")
  %"i.4" = load i32, i32* %"i"
  %".15" = add i32 %"i.4", 1
  store i32 %".15", i32* %"i"
  %"i.5" = load i32, i32* %"i"
  %".17" = icmp slt i32 %"i.5", 5
  br i1 %".17", label %"for_loop.if", label %"for_loop.endif"
entry.if:
  br label %"for_loop"
entry.endif:
  ret void
for_loop.if:
  br label %"for_loop"
for_loop.endif:
  br label %"entry.endif"
}

@"function_main_VoidType_31791" = internal constant [9 x i8] c"%d -> %d\0a"