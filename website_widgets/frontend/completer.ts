type ResolveFn<T> = (value: T | PromiseLike<T>) => void;
type RejectFn = (reason?: any) => void;

/**
A utility that mimics Dart's Completer<T>, allowing external resolution
or rejection of a Promise. Use when the logic to fulfill a promise is deferred or
triggered by external events.

Example: `RoleChecker` loads the user's role and signals when it has. A controller shows a
loading state until then, and the admin toolbar after, if the user is an admin.
```ts
class RoleChecker {
  static readonly initializedCompleter = new Completer<null>();
  private static role: string | null = null;

  // Called once, from main.ts
  static async initialize(): Promise<void> {
    try {
      const response = await fetch("/api/me/");
      RoleChecker.role = (await response.json()).role;
      RoleChecker.initializedCompleter.resolve(null);
    } catch (e) {
      RoleChecker.initializedCompleter.reject(e);
    }
  }

  static hasRole(role: string): boolean {
    return RoleChecker.role === role;
  }
}

export class AdminToolbarController extends Controller {
  private isLoading = true;
  private isAdmin = false;
  private loadingElement: HTMLElement | null = null;
  private toolbarElement: HTMLElement | null = null;

  static initializeController(): void {
    App.initializeController({ controllerClass: AdminToolbarController });
  }

  public async initState(): Promise<void> {
    this.loadingElement = this.getElementByIdOrWarn("admin-toolbar-loading");
    this.toolbarElement = this.getElementByIdOrWarn("admin-toolbar");
    // Not awaited: App calls setState() once initState() returns, so the
    // loading state shows while the role is still being fetched.
    this.waitForRole();
  }

  private async waitForRole(): Promise<void> {
    try {
      await RoleChecker.initializedCompleter.promise;
      this.isAdmin = RoleChecker.hasRole("admin");
    } catch (e) {
      console.error("Couldn't load the user's role:", e);
    }
    this.isLoading = false;
    this.setState();
  }

  public setState(): void {
    this.loadingElement?.toggleAttribute("hidden", !this.isLoading);
    this.toolbarElement?.toggleAttribute("hidden", this.isLoading || !this.isAdmin);
  }
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
