from textwrap import dedent

from bouncer.coderunners import CodeRunner
from models import Status, SubmissionRequest, TestCase
from tests.integration.config import lambda_client


class TestZig:
    def test_hello_world(self):
        test_cases = [TestCase(input='', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='zig', code={
            'main.zig': dedent('''
                const std = @import("std");

                pub fn main(init: std.process.Init) !void {
                    try std.Io.File.stdout().writeStreamingAll(init.io, "Hello World!");
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK

    def test_mixed_type_output(self):
        test_cases = [TestCase(input='', target='1 2 4 8 16 32 are powers of two')]
        request = SubmissionRequest(test_cases=test_cases, language='zig', code={
            'main.zig': dedent('''
                const std = @import("std");

                pub fn main(init: std.process.Init) !void {
                    var buffer: [64]u8 = undefined;
                    const output = try std.fmt.bufPrint(
                        &buffer,
                        "{} {} {} {} {} {} {s}",
                        .{ 1, 2, 4, 8, 16, 32, "are powers of two" },
                    );
                    try std.Io.File.stdout().writeStreamingAll(init.io, output);
                }
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '1 2 4 8 16 32 are powers of two'

    def test_compile_error(self):
        request = SubmissionRequest(test_cases=[], language='zig', code={
            'main.zig': dedent('''
                const std = @import("std");

                pub fn main(init: std.process.Init) !void {
                    const value: i32 = "Hello World!";
                    try std.Io.File.stdout().writeStreamingAll(init.io, value);
                }
            ''').strip(),
        })
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.COMPILATION_ERROR
        assert res.compile_result.status == Status.COMPILATION_ERROR

    def test_input_output_echo(self):
        test_cases = [TestCase(input='Hello World!', target='Hello World!')]
        request = SubmissionRequest(test_cases=test_cases, language='zig', code={
            'main.zig': dedent('''
                const std = @import("std");

                pub fn main(init: std.process.Init) !void {
                    var buffer: [1024]u8 = undefined;
                    const n = try std.posix.read(std.posix.STDIN_FILENO, &buffer);
                    const input = std.mem.trimEnd(u8, buffer[0..n], "\\n\\r");
                    try std.Io.File.stdout().writeStreamingAll(init.io, input);
                }
            ''').strip(),
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        print(res)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == 'Hello World!'

    def test_multi_file(self):
        test_cases = [TestCase(input='', target='2')]
        request = SubmissionRequest(test_cases=test_cases, language='zig', code={
            'main.zig': dedent('''
                const std = @import("std");
                const code = @import("dir/code.zig");

                pub fn main(init: std.process.Init) !void {
                    var buffer: [8]u8 = undefined;
                    const output = try std.fmt.bufPrint(&buffer, "{}", .{code.one() + code.one()});
                    try std.Io.File.stdout().writeStreamingAll(init.io, output);
                }
            ''').strip(),
            'ones.zig': dedent('''
                pub fn retOne() i32 {
                    return 1;
                }
            ''').strip(),
            'dir': {
                'code.zig': dedent('''
                    const ones = @import("../ones.zig");

                    pub fn one() i32 {
                        return ones.retOne();
                    }
                ''').strip(),
            },
        }, return_outputs=True)
        res = CodeRunner.from_language(language=request.language).invoke(lambda_client, request=request)
        assert res.overall.status == Status.OK
        assert res.test_results is not None and len(res.test_results) == 1 and res.test_results[0].status == Status.OK
        assert res.test_results[0].outputs.strip() == '2'
