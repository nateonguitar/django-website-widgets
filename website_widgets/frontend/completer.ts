type ResolveFn<T> = (value: T | PromiseLike<T>) => void;
type RejectFn = (reason?: any) => void;

/**
A utility that mimics Dart's Completer<T>, allowing external resolution
or rejection of a Promise. Use when the logic to fulfill a promise is deferred or
triggered by external events.

Example:
```ts
const completer = new Completer<number | null>();

// Somewhere that waits for completion:
try {
  const result = await completer.promise;
  console.log("Completed with:", result);
} catch (e) {
  console.error("Rejected with:", e);
}
// or
completer.promise
  .then((result) => console.log("Completed with:", result))
  .catch((err) => console.error("Rejected with:", err));

// Somewhere else in the code, later:
if (somethingWentWrong) {
  completer.reject("Failed due to bad state");
} else {
  completer.resolve("All done!");
}
```

The `Completer` can only be completed once. Further calls to `resolve` or `reject`
will throw an Error.
*/
export class Completer<T> {
    readonly promise: Promise<T>;
    private _resolve!: ResolveFn<T>;
    private _reject!: RejectFn;
    private _isCompleted = false;

    constructor() {
        this.promise = new Promise<T>((resolve, reject) => {
            this._resolve = (value) => {
                if (this._isCompleted) {
                    throw new Error("Completer already completed");
                }
                this._isCompleted = true;
                resolve(value);
            };
            this._reject = (reason) => {
                if (this._isCompleted) {
                    throw new Error("Completer already completed");
                }
                this._isCompleted = true;
                reject(reason);
            };
        });
    }

    get isCompleted(): boolean {
        return this._isCompleted;
    }

    resolve(value: T | PromiseLike<T>): void {
        this._resolve(value);
    }

    reject(reason?: any): void {
        this._reject(reason);
    }
}
