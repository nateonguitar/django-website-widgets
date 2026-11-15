import { beforeEach, describe, expect, it } from 'vitest';

import { App } from '../src/app.js';
import { Controller } from '../src/controller.js';

class CounterController extends Controller {
    static readonly singleton = true;
    public renders = 0;

    public setState(): void {
        this.renders += 1;
        if (this.rootElement) {
            this.rootElement.textContent = String(this.renders);
        }
    }
}

class PlainController extends Controller {}

describe('App.initController', () => {
    beforeEach(() => {
        App.clearSingletons();
        document.body.innerHTML = '<div id="counter"></div>';
    });

    it('binds the controller to the element its selector finds, then sets state', async () => {
        const counterController = new CounterController();
        const counterDiv = document.querySelector('#counter');

        await App.initController(counterController, '#counter');

        expect(counterController.rootElement).toBe(counterDiv);
        expect(counterDiv?.textContent).toBe('1');
    });

    it('registers a singleton controller only when its class says so', async () => {
        const counterController = new CounterController();
        const plainController = new PlainController();

        await App.initController(counterController, '#counter');
        await App.initController(plainController);

        const counterSingleton = App.getSingleton(CounterController);
        const plainSingleton = App.getSingleton(PlainController);
        expect(counterSingleton).toBe(counterController);
        expect(plainSingleton).toBeNull();
    });
});

describe('App.clearSingletons', () => {
    it('forgets every singleton, so the next test starts with none', async () => {
        document.body.innerHTML = '<div id="counter"></div>';
        const counterController = new CounterController();
        await App.initController(counterController, '#counter');

        App.clearSingletons();

        const counterSingleton = App.getSingleton(CounterController);
        expect(counterSingleton).toBeNull();
    });
});
