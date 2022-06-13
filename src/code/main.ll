; ModuleID = "main"
target triple = "x86_64-apple-darwin19.6.0"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

declare i32 @"scanf"(i8* %".1", ...)

define void @"main"()
{
entry:
  %"i" = alloca i32
  store i32 0, i32* %"i"
  %"i.1" = load i32, i32* %"i"
  %".3" = icmp slt i32 %"i.1", 10
  br i1 %".3", label %"entry.if", label %"entry.endif"
for_loop:
  %"i.2" = load i32, i32* %"i"
  %".6" = bitcast [3 x i8]* @"function_main_VoidType_35417" to i8*
  %".7" = call i32 (i8*, ...) @"printf"(i8* %".6", i32 %"i.2")
  %"i.3" = load i32, i32* %"i"
  %".8" = add i32 %"i.3", 1
  store i32 %".8", i32* %"i"
  %"i.4" = load i32, i32* %"i"
  %".10" = icmp slt i32 %"i.4", 10
  br i1 %".10", label %"for_loop.if", label %"for_loop.endif"
entry.if:
  br label %"for_loop"
entry.endif:
  ret void
for_loop.if:
  br label %"for_loop"
for_loop.endif:
  br label %"entry.endif"
}

@"function_main_VoidType_35417" = internal constant [3 x i8] c"%d\0a"