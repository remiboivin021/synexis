from pathlib import Path
import unittest

from synexis_brain.indexer.pipeline import run_dot_file


class PipelineRunnerTest(unittest.TestCase):
    def test_hello_pipeline_trace_and_stats(self) -> None:
        dot = Path("synexis_brain/pipelines/hello.dot")

        def hello_op(context, params):
            return {"hello": f"ok:{params.get('op')}"}

        ctx = run_dot_file(
            path=dot,
            registry={"hello_op": hello_op},
            context={"query": "hello"},
        )

        self.assertEqual(ctx["hello"], "ok:hello_op")
        self.assertEqual(ctx["_stats"]["pipeline"], "hello_pipeline")
        self.assertEqual(ctx["_stats"]["nodes_total"], 1)
        self.assertEqual(len(ctx["_trace"]), 1)
        self.assertEqual(ctx["_trace"][0]["node"], "hello")
        self.assertEqual(ctx["_trace"][0]["op"], "hello_op")


if __name__ == "__main__":
    unittest.main()
