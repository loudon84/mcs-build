"""Audit decorator for automatic audit logging."""

import functools
import time
from typing import Any, Callable

from db.repo import OrchestratorRepo
from observability.redaction import redact_dict


def audit_decorator(step_name: str):
    """Decorator to automatically audit node execution."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(state, *args, repo: OrchestratorRepo = None, **kwargs):
            start_time = time.time()
            input_state = state.model_dump() if hasattr(state, "model_dump") else state

            try:
                result = await func(state, *args, **kwargs)
                duration = time.time() - start_time
                output_state = result.model_dump() if hasattr(result, "model_dump") else result

                # Write audit event asynchronously (non-blocking)
                if repo:
                    try:
                        payload = {
                            "step": step_name,
                            "duration": duration,
                            "input": redact_dict(input_state),
                            "output": redact_dict(output_state),
                        }
                        repo.write_audit_event(
                            run_id=state.run_id if hasattr(state, "run_id") else "unknown",
                            step=step_name,
                            payload_json=payload,
                        )
                    except Exception:
                        # Audit failure should not break the flow
                        pass

                return result
            except Exception as e:
                duration = time.time() - start_time
                # Audit error
                if repo:
                    try:
                        payload = {
                            "step": step_name,
                            "duration": duration,
                            "input": redact_dict(input_state),
                            "error": str(e),
                        }
                        repo.write_audit_event(
                            run_id=state.run_id if hasattr(state, "run_id") else "unknown",
                            step=step_name,
                            payload_json=payload,
                        )
                    except Exception:
                        pass
                raise

        return wrapper

    return decorator

