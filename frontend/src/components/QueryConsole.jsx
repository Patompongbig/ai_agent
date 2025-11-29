import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postOwnerQuery } from "../api/client";

export default function QueryConsole() {
  const [message, setMessage] = useState("");
  const queryClient = useQueryClient();
  const { mutateAsync, data, isPending } = useMutation({
    mutationFn: postOwnerQuery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule"] });
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
      queryClient.invalidateQueries({ queryKey: ["machines"] });
    },
  });

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!message.trim()) {
      return;
    }
    await mutateAsync({ message });
    setMessage("");
  };

  return (
    <section className="panel">
      <header className="panel__header">
        <div>
          <h2>Owner Console</h2>
          <p>Ask anything about schedule, stock, or machines.</p>
        </div>
      </header>
      <div className="panel__body console">
        <form onSubmit={handleSubmit}>
          <label htmlFor="console-input">Prompt</label>
          <textarea
            id="console-input"
            rows={4}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="e.g. Add 100 units of widget_a before noon"
          />
          <button type="submit" disabled={isPending}>
            {isPending ? "Sending..." : "Send"}
          </button>
        </form>
        <div className="console__output">
          <h3>Latest Response</h3>
          <AgentStatus isPending={isPending} output={data?.output} />
          <AgentLog steps={data?.intermediate_steps ?? []} />
        </div>
      </div>
    </section>
  );
}

function AgentStatus({ isPending, output }) {
  if (isPending) {
    return (
      <div className="agent-status" aria-live="polite">
        <span className="agent-status__dot" />
        กำลังสั่งงาน LLM ...
      </div>
    );
  }

  if (output) {
    return (
      <div className="agent-output">
        <strong>สรุปคำตอบ:</strong>
        <p>{output}</p>
      </div>
    );
  }

  return <p>ยังไม่มีคำตอบล่าสุด</p>;
}

function AgentLog({ steps }) {
  const entries = useMemo(() => {
    return steps.map((step, index) => ({
      id: `${step.type}-${index}`,
      ...step,
    }));
  }, [steps]);

  if (!entries.length) {
    return <p className="agent-log agent-log--empty">ยังไม่มีบันทึกเครื่องมือ</p>;
  }

  return (
    <div className="agent-log">
      <h4>Agent Activity</h4>
      <ul>
        {entries.map((step) => (
          <li key={step.id} className={`agent-step agent-step--${step.type || "unknown"}`}>
            <div className="agent-step__title">
              <span className="agent-step__type">{formatStepType(step.type)}</span>
              {step.name ? <span className="agent-step__tool">{step.name}</span> : null}
            </div>
            <StepContent content={step.content} toolCalls={step.tool_calls} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function StepContent({ content, toolCalls }) {
  const parsedContent = useMemo(() => {
    if (!content) {
      return "";
    }
    try {
      const parsed = JSON.parse(content);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return content;
    }
  }, [content]);

  return (
    <>
      {parsedContent ? <pre>{parsedContent}</pre> : null}
      {Array.isArray(toolCalls) && toolCalls.length > 0 ? (
        <div className="agent-step__calls">
          {toolCalls.map((call) => (
            <code key={call.id || call.name}>
              {call.name} {call.args ? JSON.stringify(call.args) : ""}
            </code>
          ))}
        </div>
      ) : null}
    </>
  );
}

function formatStepType(type) {
  switch (type) {
    case "human":
      return "Owner";
    case "ai":
      return "LLM";
    case "tool":
      return "Tool Result";
    default:
      return "Event";
  }
}
