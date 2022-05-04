# Write-up Template

### Analyze, choose, and justify the appropriate resource option for deploying the app.

*For **both** a VM or App Service solution for the CMS app:*
- *Analyze costs, scalability, availability, and workflow*
- *Choose the appropriate solution (VM or App Service) for deploying the app*
- *Justify your choice*

### Assess app changes that would change your decision.

*Detail how the app and any other needs would have to change for you to change your decision in the last section.* 

# Comparison of Costs, Scalability, Availability and Workflow

- *Costs*: A virtual machine will produce higher costs as compared to the App Service not only for the service itself but also for maintenance because it requires patching the os and other software components e.g., the webserver. 
- *Scalability*: In a setup with one VM, the app could scale to the limits of the chosen hardware. However, it's possible to scale by using multiple VMs. In a setup with an App Service the app can scale if the App Service is configured to do so.
- *Availability*: For both the App Service and the VM the availability is dependent on the availability of the Azure resources in use and the app itself. However, with a VM the availability can be compromised by a bad configuration or outdated software running on the VM.
- *Workflow*: In general, more steps are required to get an app running in a VM compared to getting it running in an App Service.

# Choice of appropriate Solution and Justification

In this case I would choose an App Service because the app doesn't need any features that would only be available in a VM setup, and the App Service setup is cheaper and easier to maintain.

# Reasons to change to a VM Setup

I would choose the VM setup over the App Service setup if 
* the app would require additional software that is not available in the App Service e.g., a custom webserver,
* the app was re-written in a language that is not supported by the App Service in Azure,
* the app would require running background tasks and it wouldn't be an option to use a different compute service to run those background tasks or
* it would from a security point of view be required to control the underlying operating system and other software components.
